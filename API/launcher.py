import subprocess

def main():
    process1 = subprocess.Popen(['python', 'API.py'])
    process2 = subprocess.Popen(['python', 'bot.py'])
if __name__ == "__main__":
    main() 