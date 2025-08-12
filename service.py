from src import create_api 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_api(), host="localhost", port=8000)
