from flask import Flask, request, jsonify
import subprocess, threading, time, os, signal

app = Flask(__name__)

RUN_TIME = 60
RUN_COUNT = 3        # mỗi request chạy hk.py 3 lần
MAX_RUNNING = 3      # tối đa 3 request cùng lúc

running_jobs = 0
lock = threading.Lock()


def run_hk(url):
    global running_jobs
    processes = []

    try:
        for _ in range(RUN_COUNT):
            p = subprocess.Popen(
                ["python3", "hk.py", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid
            )
            processes.append(p)

        time.sleep(RUN_TIME)

    finally:
        for p in processes:
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            except:
                pass

        with lock:
            running_jobs -= 1


@app.route("/api")
def api():
    global running_jobs

    if request.args.get("type") != "view":
        return jsonify({"status": "error", "msg": "type không hợp lệ"}), 400

    url = request.args.get("url")
    if not url or not url.startswith("https://"):
        return jsonify({"status": "error", "msg": "url không hợp lệ"}), 400

    with lock:
        if running_jobs >= MAX_RUNNING:
            return jsonify({
                "status": "busy",
                "msg": f"Hệ thống đang xử lý {MAX_RUNNING} tác vụ, vui lòng chờ và thử lại sau"
            }), 429
        running_jobs += 1

    t = threading.Thread(target=run_hk, args=(url,), daemon=True)
    t.start()

    return jsonify({
        "status": "running",
        "msg": "Đang tiến hành tăng lượt xem",
        "time": "60 giây",
        "runs": RUN_COUNT
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2309)
