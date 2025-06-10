# File: github_access.py
# code on CodeBoot

# hide this file
show_file('github_access.py', False)

# download the code from github
write_file('lmc.py', read_file('https://raw.githubusercontent.com/mael-charpentier/lmc_codeboot/refs/heads/main/lmc.py'))
write_file('lmc.html', read_file('https://raw.githubusercontent.com/mael-charpentier/lmc_codeboot/refs/heads/main/lmc.html'))

# open the code in an editor
show_file('lmc.py', True)

# run the code
import lmc