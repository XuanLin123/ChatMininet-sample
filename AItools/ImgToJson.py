import json
import re


def ImgConvertTopo(
    company_name , model_name , api_key , img_path="Platform-Data/topo.jpg" , output_path="Platform-Data/topo.json" , 
    mnfile="Platform-Data/topo.mn" , default_mnfile="Platform-Data/default_mn.json"
) : 
    converters = {
        "openrouter": lambda: openrouter_ConvertToTopo(model_name, api_key, img_path),
        "openai" : lambda : print(f"Not implemented : {company_name}") ,
        "gemini" : lambda : gemini_ConvertToTopo(model_name , api_key , img_path) ,
        "claud3" : lambda : print(f"Not implemented : {company_name}") ,
        "huggin" : lambda : print(f"Not implemented : {company_name}")
    }

    result = converters.get(company_name, lambda: print(f"Unknown company : {company_name}"))()

    if not result : 
        return
    try:
        raw_text = result.text if hasattr(result, 'text') else result
        markdown_tag = "`" * 3
        pattern = rf"{markdown_tag}(?:json)?\n?|{markdown_tag}"
        clean_text = re.sub(pattern, "", raw_text).strip().lstrip('\ufeff')

        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(
                json.loads(clean_text), file, ensure_ascii=False, indent=2
            )
    except Exception as e:
        print(e)

    JsonConvertToMNFile(jsonfile=output_path , mnfile=mnfile , default_mnfile=default_mnfile)

# --------------------------------------------------------------------------------------------------------------

'''Convert json topo into mn topo'''

prompt = "This is a network topology diagram. Identify all nodes (hosts, switches) and links, and describe them in json format."
prompt += "The final JSON should have four top-level keys: 'hosts', 'switches', and 'links'."

# --- Hosts ---
prompt += "In the 'hosts' list, show the id, name, ip_address (as a single string) and x, y location of all hosts (like h1, h2, HTTP, etc.). The value of 'id' and 'name' must be exactly the same for each host."
# --- Switches ---
prompt += "In the 'switches' list, show the id, name, and x, y location of all devices depicted as switches (like s1, s2, s3). The value of 'id' and 'name' must be exactly the same for each switch."
prompt += "For each switch, determine its type: "
prompt += "If it has IP addresses assigned (e.g., 'eth0: 192.168.0.253/30'), add a 'type' field with the value 'L3_switch' and include an 'ip_addresses' list."
prompt += "If it has no IP addresses, add a 'type' field with the value 'L2_switch'."
# --- Links ---
prompt += "In the 'links' list, show the id and endpoints for all links, where the format of endpoints is [nodeA_name, nodeB_name]. Crucially, the endpoints must use the 'name' property of the corresponding node (Host, or Switch)."


def openrouter_ConvertToTopo(model_name, key, img_path):
    import base64
    from openai import OpenAI

    client = OpenAI(
        base_url = "https://openrouter.ai/api/v1",
        api_key = key,
    )

    with open(img_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    response = client.chat.completions.create(
        model = model_name,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }}]}],
        response_format={ "type": "json_object" }
    )
    result_text = response.choices[0].message.content
    return result_text


def gemini_ConvertToTopo(model_name , key , img_path) : 
    import google.generativeai as genai
    import PIL.Image

    genai.configure(api_key=key)
    model = genai.GenerativeModel(model_name)
    
    return model.generate_content([prompt , PIL.Image.open(img_path)])



def JsonConvertToMNFile(jsonfile="Platform-Data/topo.json", mnfile="Platform-Data/topo.mn" , default_mnfile="Platform-Data/default_mn.json"):
    with open(jsonfile , 'r') as file : 
        JsonFileInfo = json.load(file)

    with open(default_mnfile , 'r') as file : 
        Default_MNinfo = json.load(file)


    JsonFileInfo["application"] = JsonFileInfo.get("application", Default_MNinfo["application"])
    keys = ["dpctl", "ipBase", "netflow", "openFlowVersions", "sflow", "startCLI", "switchType", "terminalType"]
    for key in keys:
        JsonFileInfo["application"][key] = JsonFileInfo["application"].get(key, Default_MNinfo["application"][key])

    
    for index , host in enumerate(JsonFileInfo.get("hosts", []) , start=1) : 
        Default_MNinfo["hosts"].append(
            {
                "number" : str(index) ,
                "opts"   : 
                {
                    "hostname" : host["name"] ,
                    "nodeNum"  :  index       ,
                    "ip"       : host.get("ip_address" , "127.0.0.1") , 
                    "nodeType" : "Host"       ,
                    "sched"    : "host"
                } ,
                "x" : host.get("x" , str(55  + index * 200)),
                "y" : host.get("y" , str(224 + index * 0  ))
            }
        )


    for index , switch in enumerate(JsonFileInfo.get("switches" , []) , start=1) : 
        if switch.get("type") == "L3":
            ip_addresses = switch.get("ip_addresses", [])
            primary_ip = ip_addresses[0].split("/")[0] if ip_addresses else "127.0.0.1"
            
            Default_MNinfo["switches"].append(
                {
                    "number" : str(len(Default_MNinfo["switches"]) + 1) ,
                    "opts"   : 
                    {
                        "hostname" : switch["name"] ,
                        "nodeNum"  : len(Default_MNinfo["switches"]) + 1 ,
                        "ip"       : primary_ip , 
                        "nodeType" : "L3Switch"   ,
                        "isRouter" : True       ,
                        "isL3Switch": True      ,
                        "ip_addresses" : ip_addresses
                    } ,
                    "x" : switch.get("x" , str(55  + index * 200)),
                    "y" : switch.get("y" , str(224 + index * 0  ))
                }
            )
        else:
            Default_MNinfo["switches"].append(
                {
                    "number" : str(index) , 
                    "opts" : 
                    {
                        "controllers" :     []  ,
                        "hostname"    : switch["name"],
                        "netflow"     :    "0"  ,
                        "nodeNum"     :   index ,
                        "sflow"       :    "0"  ,
                        "switchIP"    :    ""   ,
                        "switchType"  : "default"
                    } ,
                    "x" : switch.get("x" , str(192 + index * 200)),
                    "y" : switch.get("y" , str(334 + index * 0  ))
                }
            )


    id_to_name = {} 
    for host in JsonFileInfo.get("hosts", []):
        id_to_name[host["id"]] = host["name"]
    
    for switch in JsonFileInfo.get("switches", []):
        id_to_name[switch["id"]] = switch["name"]

    for link in JsonFileInfo.get("links", []):
        src_id = link["endpoints"][0]
        dest_id = link["endpoints"][1]
        
        src_name = id_to_name.get(src_id, src_id)
        dest_name = id_to_name.get(dest_id, dest_id)

        link_opts = {}
        if "params" in link:
            link_opts.update(link["params"])

        Default_MNinfo["links"].append(
            {
                "src": src_name,
                "dest": dest_name,
                "opts": link_opts
            }
        )


    with open(mnfile , 'w') as file : 
        json.dump(Default_MNinfo, file, indent=4)

    print(f"MN topology file '{mnfile}' generated successfully!")


if __name__ == "__main__" : 
    with open('../Platform-Data/platform-params.json' , 'r') as file : 
        PlatformParams = json.load(file)
