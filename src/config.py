config = {
    "user_agents": [
        {
            "desktop": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
        {
            "mobile": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"}
    ],
    "languages": [
        {"de": "de;en;q=0.6"},
        {"fr": "fr;en;q=0.6"},
        {"it": "it;en;q=0.6"},
    ],
    "expected_headers": {
        "X-XSS-Protection": lambda value: "Strong" if "1; mode=block" in value.lower() else "Weak",
        "X-Frame-Options": lambda value: "Strong" if value.lower() in ["deny", "sameorigin"] else "Weak",
        "X-Content-Type-Options": lambda value: "Strong" if value.lower() == "nosniff" else "Weak",
        "Referrer-Policy": lambda value: (
            "Strong" if (
                    value.lower() in ["no-referrer", "same-origin", "strict-origin-when-cross-origin"]
            )
            else "Weak"
        ),
        "Access-Control-Allow-Origin": lambda value: (
            "Weak" if (
                    "*" in value.lower() or "null" in value.lower()
            )
            else "Strong"
        ),
        "Strict-Transport-Security": lambda value: (
            "Strong" if (
                    "max-age=" in value.lower()
                    and int(value.lower().split('max-age=')[1].split(';')[0]) >= 31536000
                    and ("includesubdomains" in value.lower()
                    or ("includesubdomains" in value.lower() and "preload" in value.lower()))
            )
            else "Weak"
        ),
        "Content-Security-Policy": lambda value: (
            "Strong" if (
                    "default-src 'self'" in value.lower()
                    and "form-action 'self'" in value.lower()
                    and "object-src 'none'" in value.lower()
                    and "upgrade-insecure-requests" in value.lower()
                    and "block-all-mixed-content" in value.lower()
                    and "unsafe-eval" not in value.lower()
                    and (
                            "unsafe-inline" not in value.lower()
                            or "nonce-" in value.lower()
                            or "hash-" in value.lower()
                    )
                    and value.lower() in ["frame-ancestors 'self'", "frame-ancestors 'none'"]
                    and "https://*" not in value.lower()
            )
            else "Weak"
        ),
        "cross-origin-resource-policy": lambda value: "Strong" if value.lower() in ["same-origin",
                                                                                    "same-site"] else "Weak",
        "cross-origin-embedder-policy": lambda value: "Strong" if value.lower() in ["require-corp",
                                                                                    "credentialless"] else "Weak",
        "cross-origin-opener-policy": lambda value: "Strong" if (
                value.lower() in ["same-origin", "same-origin-allow-popups"]
        ) else "Weak",
        "Set-Cookie": lambda value: (
            "Strong" if (
                "secure" in value.lower() and
                ("samesite=strict" in value.lower() or "samesite=lax" in value.lower()) and
                "httponly" in value.lower()
            ) else "Weak"
        ),
    },
    "deprecated_headers": ["X-XSS-Protection", "X-Frame-Options"],
    "critical_headers": ["Strict-Transport-Security", "Content-Security-Policy"],
    "header_multipliers": {
        "Strict-Transport-Security": 2,
        "Content-Security-Policy": 1.8,
        "cross-origin-embedder-policy": 1.5,
        "cross-origin-resource-policy": 1.5,
        "cross-origin-opener-policy": 1.5,
        "X-Frame-Options": 0.8,
        "X-XSS-Protection": 0.8,
    },
    "timeout": 60,
    "max_threads": 5,
    "daily_assessments": 1,
    "basic_point_unit": 10,
}
