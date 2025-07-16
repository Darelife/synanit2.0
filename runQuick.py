from ContestGraphImageGenerator import ContestGraphImageGenerator
import time
import threading
if __name__ == "__main__":
    def run_generation(contestId, descText, imageSelected, regex, overrideContestName, overrideText):
        stop_spinner = False
        start = time.time()
        generator = ContestGraphImageGenerator(
            contestId=contestId,
            descText=descText,
            imageSelected=imageSelected,
            regex=regex,
            overrideContestName=overrideContestName,
            overrideText=overrideText
        )

        def spinner():
            dots = ""
            while not stop_spinner:
                dots = "." if len(dots) >= 3 else dots + "."
                print(f"\r\033[93mProcessing{dots}  \033[0m", end="", flush=True)
                time.sleep(0.5)
            print("\r", end="")

        t = threading.Thread(target=spinner)
        t.start()

        generator.generate()
        stop_spinner = True

        t.join()

        print(f"\033[94mThe operation took {(time.time() - start):.2f} seconds\033[0m")

    params = [
        (2119, "TOP 5 - Overall", 0, r"^(2023|2024|2022).{9}$", True, "CODEFORCES Div.2 ROUND 1035"),
        (2119, "TOP 5 - 2023 Batch", 2, r"^(2023).{9}$", True, "CODEFORCES Div.2 ROUND 1035"),
        (2119, "TOP 5 - 2022 Batch", 3, r"^(2022).{9}$", True, "CODEFORCES Div.2 ROUND 1035"),
        (2119, "TOP 5 - 2024 Batch", 1, r"^(2024).{9}$", True, "CODEFORCES Div.2 ROUND 1035")
    ]

    for p in params:
        run_generation(*p)
