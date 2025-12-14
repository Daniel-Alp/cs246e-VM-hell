import argparse
import libtmux
import time
from pathlib import Path

translate = {
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
    "bs": "^?",
    "esc": "Escape"
}

def to_snap_path(test_path: Path) -> Path:
    return Path("snapshots") / test_path.relative_to("tests").with_suffix(".out")

def test(test_path: str, pane: libtmux.Pane) -> str:
    with open(test_path, "r") as test_file:        
        str = "".join(c.rstrip() for c in test_file.readlines())
        tokens = []
        token = ""
        i = 0
        while i < len(str):
            if str[i] == "<":
                tokens.append((token, True))
                token = ""
                i += 1
                while str[i] != ">":
                    token += str[i] 
                    i += 1
                i += 1
                tokens.append((token, False))
                token = ""
            else:
                token += str[i]
                i += 1
        if token:
            tokens.append((token, True))
        tokens = [(bytes(token, "utf-8").decode("unicode escape"), is_normal) 
                  for (token, is_normal) in tokens]
        for (token, is_normal) in tokens:
            if is_normal:
                if ";" in token:
                    for c in token:
                        if c == ";":
                            c = "\\;"
                        pane.send_keys(c, literal=True, enter=False)
                        time.sleep(0.05)
                else:
                    pane.send_keys(token, literal=True, enter=False)
                    time.sleep(0.05)
            else:
                parts = token.split()
                repeat = int(parts[1]) if len(parts) == 2 else 1
                token = translate[parts[0]]
                for _ in range(repeat):
                    pane.send_keys(token, literal=False, enter=False)
                    time.sleep(0.025)
    return [line.rstrip() for line in pane.capture_pane()]

def run():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-test", type=str)
    group.add_argument("--diff", action="store_true")
    group.add_argument("--upgrade", action="store_true")
    group.add_argument("--clean", action="store_true")

    args = parser.parse_args()
    server = libtmux.Server()
    if args.clean:
        # delete tests
        snap_paths_keep = set([to_snap_path(path) for path in Path("tests").glob("**/*") if path.is_file()])
        snap_paths_all = set([path for path in Path("snapshots").glob("**/*") if path.is_file()])
        snap_paths_clean = snap_paths_all - snap_paths_keep
        for snap_path in snap_paths_clean:  
            print(f"\033[32munlink: {snap_path}\033[0m")  
            snap_path.unlink()
        # delete empty directories
        dirs_clean = [dir for dir in Path("snapshots").glob("**/*") if (not dir.is_file()) and (not any(dir.iterdir()))]
        for dir in dirs_clean:
            print(f"\033[32mrmdir: {dir}\033[0m")  
            dir.rmdir()
        return
    if args.run_test:
        session = server.new_session(
            session_name="vm",
            kill_session=True,
            attach=False,
            window_command="./vm"
        )
        print("\n".join(test(args.run_test, session.active_window.active_pane)))
        return
    for test_path in Path("tests").glob("**/*"):
        if not Path(test_path).is_file():
            continue
        snap_path = to_snap_path(test_path)
        if args.diff:
            if not Path(snap_path).exists():
                print(f"\033[31msnapshot does not exist: {snap_path}\033[0m")
                continue
            time.sleep(0.5)
            session = server.new_session(
                session_name="vm",
                kill_session=True,
                attach=False,
                window_command="./vm"
            )
            with open(snap_path, "r") as snap_file:
                new_lines = test(test_path, session.active_window.active_pane)
                old_lines = [line.rstrip() for line in snap_file.readlines()]
                if "\n".join(new_lines[0:-1]) != "\n".join(old_lines[0:-1]):
                    #fail
                    print(f"\033[31m{test_path}\033[0m")
                else:
                    row_new, col_new = new_lines[-1].split()[-1].split(",")
                    row_old, col_old = old_lines[-1].split()[-1].split(",")
                    if row_new == row_old and (col_new == col_old or (col_new == "0-1" and col_old == "1-1")):
                        #pass
                        print(f"\033[32m{test_path}\033[0m")
                    else:
                        #fail
                        print(f"\033[31m{test_path}\033[0m")
        elif args.upgrade:       
            snap_path.parent.mkdir(parents=True, exist_ok=True)
            with open(snap_path, "w") as snap_file:
                print(f"\033[32mupgrade: {snap_path}\033[0m")
                snap_file.write(test(test_path, session.active_window.active_pane))

run()
