def main() -> None:
    import uvicorn

    uvicorn.run(
        "tutoring_manager_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
