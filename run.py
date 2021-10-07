from manager import app 
from werkzeug.serving import run_simple
from configuration import DEBUG , HOST, PORT

if __name__ == "__main__": 
    run_simple (
        HOST,
        PORT,
        app,
        use_reloader= True ,
        use_debugger=DEBUG,
        use_evalex = True 
        )


"""

if __name__ == "__main__": 
    
    PARSER = argparse.ArgumentParser(
        description="Arab-Bank-Phonotics")

    PARSER.add_argument('--debug', action='store_true',
                        help="Use flask debug/dev mode with file change reloading")
    ARGS = PARSER.parse_args()

    PORT = int(os.environ.get('PORT', 5000))
    HOST = "0.0.0.0"
    DEBUG = True 

    if ARGS.debug:
        print("Running in debug mode")
        CORS = CORS(APP)
        app.run(host=HOST, port=PORT, debug=DEBUG)
    else:
        app.run(host=HOST, port=PORT, debug=DEBUG)

"""


