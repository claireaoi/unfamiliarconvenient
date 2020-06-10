PUTTING STUFF IN PLACE

1) Copy requirements.txt, runInteract.sh, runSelfQuest.sh, and the
  'workshop' folder to ~/mycroft-core

2) Copy the content from INSIDE _skills folder to ~/opt/mycroft/skills/
      opt folder is not visible by default
      right-click anywhere on your window, click Open Terminal
      type line by line, pressing enter at each time:
      cd
      cd /opt/mycroft/skills
      nautilus .
      (mind the dot)
      Now you can copy the skills via a graphical interface

3. Go back to terminal, again, line-by-line:
      cd
      cd mycroft-core
      sudo apt-get install python3-dev graphviz libgraphviz-dev pkg-config
      source .venv/bin/activate
      pip3 install -r requirements.txt

4. There's one last minor bug that we need to fix. Through the graphic interface,
    go to folder:
      home/mycroft-core/.venv/lib/python3.6/site-packages/sematch/semantic/
      open the file sparql.py with a text editor
      in line 36, put parentheses:
      print(query) instead of print query
      save
