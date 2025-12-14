# Setting up
```
apt install tmux
virtualenv venv
. venv/bin/activate
python3 -m pip install -r requirements.txt
tmux new-session -d -n vm -s vm
```
If you are using Visual Studio Code, you can do `ctrl+shift+P` and type `Python: Create Environment` to create a `venv`. \
If you are on MacOS to install tmux do `brew install tmux`. \
If you are on Windows, change your operating system. \
Copy your executable, which has to be called `vm`, into the project directory, and give it executable permissions. 
```
chmod 777 vm
```
you will get strange errors if you don't do this (tmux will say it failed to create a session). \
To test your implementation against my snapshots, do:
```
python3 test.py --diff
```
If you want to run a specific test and check its output, do:
```
python3 test.py --run-test path/to/test/case.in
```
# About the tester
The tester works by running your program and using tmux to send keys to the program, 
then capturing the contents of the terminal screen and comparing it to the snapshots.

Obviously, there may be differences in how the programs display their output. tmux already takes care of 
removing any color, bold, etc. The main difference is what we draw in the status line (line at the bottom of the screen). 

The way I compare the screen to the snapshot is by making sure the top $n-1$ lines are identical, and then check that the cursor
info is correct. To check that the cursor info is correct, I try to look for the `row,col-vcol` pattern on the screen, and assume
it is the rightmost item on the status line. I also treat cases like `row,0-1` and `row,1` identically (this is not entirely true to vim but it keeps things simple). 

Last thing: my program is not vim compliant in all cases, because that is too difficult, but I tried to only feature tests where my program produced output that was the same as vim.

# About writing your own tests
If you look at the format of the `.in` files you might see something like this
```
ifoobar\nhello, world!<esc>
```
Some things to note: if you want to type a newline you have to type `\n` explicitly 
(and I would recommend doing `\t` for tabs). 
Newlines at the end of a line are ignored, so
```
i
foobar\n
hello, world!
<esc>
```
is the same as the test case above.
To test arrow keys, backspace, and escape, you do 
```
<left> <right> <up> <down> <bs> <esc>
```
You can also add a multiplier for these special keys, e.g. `<bs 4>`.
I don't support escaping `<` so it's best you don't type `<` as that will be interpreted as the start of a `<special key>`.