"""一键运行测试脚本"""
import pytest
import sys
import os

# 将项目根目录加入 path
sys.path.insert(0, os.path.dirname(__file__))


def main():
    args = [
        "tests/",
        "-v",
        "-s",
        "--tb=short",
        # 如需 Allure 报告，取消下方注释
        # "--alluredir=reports/allure-results",
    ]

    # 支持命令行传入额外参数
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])

    exit_code = pytest.main(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
