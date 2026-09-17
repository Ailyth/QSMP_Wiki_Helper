from gui.gui import run_app
from service import refresh_data

def main():
    result = refresh_data()
    run_app(result.creators, result.merged_data, result.vod_mismatches)

if __name__ == "__main__":
    main()