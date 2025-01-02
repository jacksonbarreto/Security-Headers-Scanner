class ScanResult:
    def __init__(self, initial_status=None, final_status=None, redirect_count=0, headers=None, protocol=None, final_url=None):
        self.initial_status = initial_status
        self.final_status = final_status
        self.redirect_count = redirect_count
        self.headers = headers or {}
        self.protocol = protocol or "Unknown"
        self.final_url = final_url

    def __repr__(self):
        return (f"ScanResult(initial={self.initial_status}, final={self.final_status}, "
                f"redirects={self.redirect_count}, protocol={self.protocol}, "
                f"final_url={self.final_url}, headers={len(self.headers)} headers)")
