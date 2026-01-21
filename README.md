# ChatMininet Sample 

An LLM-powered network simulation tool built on Mininet and RESTful APIs, allowing users to configure and control networks via a conversational interface.

## Necessary Dependencies

**Core Component: Containernet**

This project relies on [Containernet](https://github.com/containernet/containernet) as its core simulation engine. Please ensure it is properly installed before proceeding.

Please follow the official installation procedure provided by Containernet to set up the environment:
1. System Dependencies & Source Code
    ```bash
    sudo apt-get install ansible
    git clone https://github.com/containernet/containernet.git
    ```
2. System wide Installation (Ansible)
    ```bash
    sudo ansible-playbook -i "localhost," -c local containernet/ansible/install.yml
    ```
3. Python Environment Setup
    ```bash
    python3 -m venv venv
    source venv/bin/activate

    # Option A: Install in "Edit" mode (Recommended for developers)
    pip install -e . --no-binary :all:

    # Option B: Install in "Normal" mode
    pip install .
    ```

## How to use

1. Clone this project

    ```bash
    git clone https://github.com/XuanLin123/ChatMininet-sample.git
    ```
2. Set up API key (Support gemini api key)

    a. Image-to-Topology: Automated environment generation from network diagrams
    ```bash
    # setting gemini api key
    gedit ChatMininet-sample/Platform-Data/platform-params.json
    ```
    b. Chat with the agent after the environment starts
    ```bash
    # setting gemini api key
    gedit ChatMininet-sample/MCPserver/adk_agent/.env
    ```

3. Activate the previously created virtual environment

    ```bash
    source venv/bin/activate
    ```
4. Enter the project folder and execute the program
    ```bash
    cd ChatMininet-sample

    sudo python3 Platform.py
    or
    sudo ~/Desktop/venv/bin/python3 Platform.py
    ```


## demo video

to be updated

