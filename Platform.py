import os
import json
import traceback

from AItools.ImgToJson        import *
from Network.AIRestAPI        import AI_MininetRest

def main(PlatformParams , Network) : 
    try : 
        Network      . StartUp    (term_enable = True , visualize_enable = True )

    except Exception as e : 
        print(f"<< Platform.py -- main() >> error occurred : {e}")
        traceback.print_exc()

    finally : 
        Network     .ShutDown ( )
        os          ._exit    (1)

if __name__ == '__main__' : 
    with open('Platform-Data/platform-params.json' , 'r') as file : 
        PlatformParams = json.load(file)

    jsonfile = ImgConvertTopo(
        "openrouter"   , 
        PlatformParams["Model-Name"]["gemini"] , 
        PlatformParams["API-Key"]   ["openrouter"] , 
        img_path="Platform-Data/topo.jpg"
    )

    Network = AI_MininetRest()

    main(PlatformParams , Network)
