from setuptools import setup, find_packages

setup(
    name="calendar-sse-mcp",
    version="0.1.0",
    description="A Model Context Protocol server for macOS Calendar.app",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "mcp>=1.7.1",
        "starlette>=0.46.2",
        "python-dotenv>=1.0.0",
        "pyobjc-framework-EventKit>=9.0",
        "pyobjc-core>=9.0",
        "pyobjc-framework-Cocoa>=9.0",
    ],
    python_requires=">=3.12",
    entry_points={
        "console_scripts": [
            "calendar-mcp=calendar_sse_mcp.__main__:main",
        ],
    },
) 