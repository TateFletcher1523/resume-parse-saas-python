import json
import sys

from resume_parser import ResumeParser, hiring_decision


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python src/run_resume_parse.py resume.pdf")
    with open(sys.argv[1], "rb") as handle:
        parsed = ResumeParser().parse_pdf(handle.read())
    result = {"profile": parsed, "next_step": hiring_decision(parsed)}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

