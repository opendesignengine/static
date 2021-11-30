import sys
from holoseat import app

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if len(args) and (args[0] == '-d'):
        app.start(debug=True)
    else:
        app.start(debug=False)

if __name__ == "__main__":
    main()
