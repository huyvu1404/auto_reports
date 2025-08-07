from src import create_app
import asyncio

def main():
    asyncio.run(create_app(headless=False))

if __name__ == "__main__":
    main()
