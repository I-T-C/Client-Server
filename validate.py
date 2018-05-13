
def main():
    ip = validateIp()

    while ip is not True:
        print("incorect")
        ip = validateIp()


def validateIp():
    ip = input("What is the ip address: ")
    a = ip.split('.')
    
    if len(a) != 4:
        return False

    for x in a:
        if x.isdigit():
            if int(x) < 0 or int(x) > 255:
                return False

    return True   

def validateURL():
    url = input("What is the URL: ")
    a = url.split('.')

    if len(a) < 2 or len(a[-1]) > 3:
        return False
    
    return True

main()