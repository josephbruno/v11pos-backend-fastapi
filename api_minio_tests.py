import base64
import csv
import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000/api").rstrip("/")
ALT_BASE_URLS = list({
    BASE_URL,
    BASE_URL.replace("/api", "/api/v1"),
    "http://localhost:8000/api/v1",
})

EMAIL = os.getenv("API_EMAIL", "superadmin@restaurant.com")
PASSWORD = os.getenv("API_PASSWORD", "Admin@123")
RESTAURANT_ID = os.getenv("RESTAURANT_ID", "")

LOG_ROOT = "logs"
CSV_PATH = "api_test_results.csv"

SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json"})


@dataclass
class TestResult:
    test_id: str
    module: str
    operation: str
    endpoint: str
    method: str
    expected_status: int
    actual_status: int
    result: str
    response_time: float
    request_file: str
    response_file: str
    remarks: str


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def write_request_log(path: str, endpoint: str, method: str, headers: Dict, payload: str) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"endpoint: {endpoint}\n")
        f.write(f"method: {method}\n")
        f.write("headers:\n")
        for k, v in headers.items():
            f.write(f"  {k}: {v}\n")
        f.write("payload:\n")
        f.write(payload)
        f.write("\n")


def write_response_log(path: str, status_code: int, body: str, response_time: float) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"status_code: {status_code}\n")
        f.write(f"response_time: {response_time:.3f}s\n")
        f.write("response_body:\n")
        f.write(body)
        f.write("\n")


def download_image(path: str) -> None:
    url = f"https://picsum.photos/seed/{uuid.uuid4().hex}/600/400"
    try:
        resp = SESSION.get(url, timeout=20)
        resp.raise_for_status()
        with open(path, "wb") as f:
            f.write(resp.content)
        return
    except Exception:
        png_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNg"
            "YAAAAAMAAWgmWQ0AAAAASUVORK5CYII="
        )
        with open(path, "wb") as f:
            f.write(base64.b64decode(png_b64))


def parse_json(resp: requests.Response) -> Tuple[Optional[dict], str]:
    try:
        return resp.json(), resp.text
    except Exception:
        return None, resp.text


def try_request(method: str, url: str, **kwargs) -> Tuple[requests.Response, float]:
    start = time.perf_counter()
    resp = SESSION.request(method, url, **kwargs)
    elapsed = time.perf_counter() - start
    return resp, elapsed


def login() -> Tuple[str, str, str]:
    login_paths = ["/login", "/auth/login", "/auth/login/"]
    payload = {"email": EMAIL, "password": PASSWORD}

    for base in ALT_BASE_URLS:
        for path in login_paths:
            url = f"{base}{path}"
            resp, _ = try_request("POST", url, data=payload)
            data, _ = parse_json(resp)
            token = None
            if data and isinstance(data, dict):
                token = (
                    data.get("data", {}).get("access_token")
                    if isinstance(data.get("data"), dict)
                    else data.get("access_token")
                )
            if resp.status_code in (200, 201) and token:
                return token, url, base
    raise RuntimeError("Login failed on all known endpoints")


def get_restaurant_id(base: str, headers: Dict) -> Optional[str]:
    paths = ["/restaurants/my-restaurants", "/restaurants/my-restaurants/"]
    for path in paths:
        url = f"{base}{path}"
        resp, _ = try_request("GET", url, headers=headers)
        data, _ = parse_json(resp)
        if resp.status_code == 200 and data and isinstance(data.get("data"), list) and data["data"]:
            return data["data"][0].get("id")
    return None


def resolve_endpoint(base: str, candidates: List[str], method: str, headers: Dict, **kwargs) -> Tuple[str, requests.Response, float, str]:
    last_resp = None
    last_time = 0.0
    last_url = ""
    for path in candidates:
        url = f"{base}{path}"
        resp, elapsed = try_request(method, url, headers=headers, **kwargs)
        if resp.status_code not in (404,):
            return url, resp, elapsed, ""
        last_resp, last_time, last_url = resp, elapsed, url
    return last_url, last_resp, last_time, "Endpoint fallback used; last attempt returned 404"


def run_test(module: str, operation: str, method: str, base: str, paths: List[str],
             expected_status: int, headers: Dict, payload_desc: str, **kwargs) -> Tuple[TestResult, Optional[dict]]:
    test_id = uuid.uuid4().hex[:8]
    request_file = os.path.join(LOG_ROOT, module, f"{operation}_{test_id}_request.txt")
    response_file = os.path.join(LOG_ROOT, module, f"{operation}_{test_id}_response.txt")

    url, resp, elapsed, remark = resolve_endpoint(base, paths, method, headers, **kwargs)
    data, body_text = parse_json(resp)
    remark = remark or ""
    if data is None:
        remark = (remark + " | " if remark else "") + "Invalid JSON response"

    write_request_log(request_file, url, method, headers, payload_desc)
    write_response_log(response_file, resp.status_code, body_text, elapsed)

    result = "PASS" if resp.status_code == expected_status and data is not None else "FAIL"

    test_result = TestResult(
        test_id=test_id,
        module=module,
        operation=operation,
        endpoint=url,
        method=method,
        expected_status=expected_status,
        actual_status=resp.status_code,
        result=result,
        response_time=elapsed,
        request_file=request_file,
        response_file=response_file,
        remarks=remark,
    )

    return test_result, data


def append_csv(results: List[TestResult]) -> None:
    file_exists = os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "test_id",
                "module",
                "operation",
                "endpoint",
                "method",
                "expected_status",
                "actual_status",
                "result",
                "response_time",
                "request_file",
                "response_file",
                "remarks",
            ])
        for r in results:
            writer.writerow([
                r.test_id,
                r.module,
                r.operation,
                r.endpoint,
                r.method,
                r.expected_status,
                r.actual_status,
                r.result,
                f"{r.response_time:.3f}",
                r.request_file,
                r.response_file,
                r.remarks,
            ])


def get_id(data: Optional[dict]) -> Optional[str]:
    if not data:
        return None
    if isinstance(data.get("data"), dict):
        return data["data"].get("id")
    return data.get("id")


def main() -> None:
    ensure_dir(LOG_ROOT)

    token, _, base = login()
    headers = {"Authorization": f"Bearer {token}"}
    restaurant_id = RESTAURANT_ID or get_restaurant_id(base, headers)
    if not restaurant_id:
        raise RuntimeError("Unable to resolve restaurant_id; set RESTAURANT_ID env var")

    results: List[TestResult] = []
    failures: List[str] = []

    ensure_dir("/tmp/api_images")
    img1 = f"/tmp/api_images/{uuid.uuid4().hex}.jpg"
    img2 = f"/tmp/api_images/{uuid.uuid4().hex}.jpg"
    img3 = f"/tmp/api_images/{uuid.uuid4().hex}.jpg"
    download_image(img1)
    download_image(img2)
    download_image(img3)

    # CATEGORY
    category_name = f"Cat-{uuid.uuid4().hex[:6]}"
    category_slug = f"cat-{uuid.uuid4().hex[:6]}"

    create_paths = ["/products/categories", "/products/categories/"]
    with open(img1, "rb") as f1:
        files = {"image": f1}
        data = {
            "restaurant_id": restaurant_id,
            "name": category_name,
            "slug": category_slug,
            "description": "Test category with image",
        }
        payload_desc = json.dumps({"fields": data, "files": {"image": os.path.basename(img1)}})

        cat_result, cat_resp = run_test(
            module="category",
            operation="create",
            method="POST",
            base=base,
            paths=create_paths,
            expected_status=200,
            headers=headers,
            payload_desc=payload_desc,
            files=files,
            data=data,
        )
        results.append(cat_result)
        cat_id = get_id(cat_resp)

    if not cat_id:
        failures.append("category_create")
    else:
        update_paths = [f"/products/categories/{cat_id}"]
        with open(img2, "rb") as f2:
            files = {"image": f2}
            data = {"description": "Updated category image"}
            payload_desc = json.dumps({"fields": data, "files": {"image": os.path.basename(img2)}})

            upd_result, _ = run_test(
                module="category",
                operation="update",
                method="PUT",
                base=base,
                paths=update_paths,
                expected_status=200,
                headers=headers,
                payload_desc=payload_desc,
                files=files,
                data=data,
            )
            results.append(upd_result)

        del_paths = [f"/categories/{cat_id}", f"/products/categories/{cat_id}"]
        del_result, _ = run_test(
            module="category",
            operation="delete",
            method="DELETE",
            base=base,
            paths=del_paths,
            expected_status=200,
            headers=headers,
            payload_desc="",
        )
        results.append(del_result)

    # PRODUCT
    product_name = f"Prod-{uuid.uuid4().hex[:6]}"
    product_slug = f"prod-{uuid.uuid4().hex[:6]}"

    create_paths = ["/products", "/products/"]
    with open(img1, "rb") as f1:
        files = {"image": f1}
        data = {
            "restaurant_id": restaurant_id,
            "category_id": cat_id or restaurant_id,
            "name": product_name,
            "slug": product_slug,
            "sku": f"SKU-{uuid.uuid4().hex[:6]}",
            "price": 1000,
        }
        payload_desc = json.dumps({"fields": data, "files": {"image": os.path.basename(img1)}})

        prod_result, prod_resp = run_test(
            module="product",
            operation="create",
            method="POST",
            base=base,
            paths=create_paths,
            expected_status=200,
            headers=headers,
            payload_desc=payload_desc,
            files=files,
            data=data,
        )
        results.append(prod_result)
        prod_id = get_id(prod_resp)

    if not prod_id:
        failures.append("product_create")
    else:
        update_paths = [f"/products/{prod_id}"]
        with open(img3, "rb") as f3:
            files = {"image": f3}
            data = {"description": "Updated product image"}
            payload_desc = json.dumps({"fields": data, "files": {"image": os.path.basename(img3)}})

            upd_result, _ = run_test(
                module="product",
                operation="update",
                method="PUT",
                base=base,
                paths=update_paths,
                expected_status=200,
                headers=headers,
                payload_desc=payload_desc,
                files=files,
                data=data,
            )
            results.append(upd_result)

        del_paths = [f"/products/{prod_id}"]
        del_result, _ = run_test(
            module="product",
            operation="delete",
            method="DELETE",
            base=base,
            paths=del_paths,
            expected_status=200,
            headers=headers,
            payload_desc="",
        )
        results.append(del_result)

    # MODIFIERS
    modifier_name = f"Mod-{uuid.uuid4().hex[:6]}"

    create_paths = ["/products/modifiers"]
    with open(img2, "rb") as f2:
        files = {"icon": f2}
        data = {
            "restaurant_id": restaurant_id,
            "name": modifier_name,
            "type": "single",
        }
        payload_desc = json.dumps({"fields": data, "files": {"icon": os.path.basename(img2)}})

        mod_result, mod_resp = run_test(
            module="modifier",
            operation="create",
            method="POST",
            base=base,
            paths=create_paths,
            expected_status=200,
            headers=headers,
            payload_desc=payload_desc,
            files=files,
            data=data,
        )
        results.append(mod_result)
        mod_id = get_id(mod_resp)

    if not mod_id:
        failures.append("modifier_create")
    else:
        update_paths = [f"/products/modifiers/{mod_id}"]
        with open(img1, "rb") as f1:
            files = {"icon": f1}
            data = {"name": f"{modifier_name}-updated"}
            payload_desc = json.dumps({"fields": data, "files": {"icon": os.path.basename(img1)}})

            upd_result, _ = run_test(
                module="modifier",
                operation="update",
                method="PUT",
                base=base,
                paths=update_paths,
                expected_status=200,
                headers=headers,
                payload_desc=payload_desc,
                files=files,
                data=data,
            )
            results.append(upd_result)

        del_paths = [f"/products/modifiers/{mod_id}"]
        del_result, _ = run_test(
            module="modifier",
            operation="delete",
            method="DELETE",
            base=base,
            paths=del_paths,
            expected_status=200,
            headers=headers,
            payload_desc="",
        )
        results.append(del_result)

    append_csv(results)

    total = len(results)
    passed = sum(1 for r in results if r.result == "PASS")
    failed = total - passed

    print("total_tests", total)
    print("passed", passed)
    print("failed", failed)
    print("csv_path", CSV_PATH)

    if failures:
        print("failures", ", ".join(failures))


if __name__ == "__main__":
    main()
