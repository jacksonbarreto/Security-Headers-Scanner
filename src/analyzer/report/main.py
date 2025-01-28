from src.analyzer.report.http_version import make_http_version_adoption
from src.analyzer.report.inconsistency import make_inconsistencies
from src.analyzer.report.score_analyzer import score_analyze

def generate_reports():
    score_analyze()
    make_inconsistencies()
    make_http_version_adoption()

if __name__ == "__main__":
    generate_reports()
