from tkinter import Button, Toplevel, Label, StringVar, Entry, Tk
import tkinter as tk
import threading, subprocess
from host import main as host_main, add_user # type: ignore
from client import main as client_main # type: ignore

def destroy(t):
    t.destroy()

def start_client(ip,dusr,dpasswd):
    usr = dusr.get()
    passwd = dpasswd.get()
    dusr.clipboard_clear()
    client_thread = threading.Thread(target=lambda: client_main(ip,usr,passwd))
    client_thread.start()

def start_host():
    host_thread = threading.Thread(target=host_main)
    host_thread.start()

def add_new_user(dnewusr,dnewpasswd,dnewtime):
    newusr = dnewusr.get()
    newpasswd = dnewpasswd.get()
    newtime = int(dnewtime.get())
    dnewusr.clipboard_clear()
    dnewpasswd.clipboard_clear()
    dnewtime.clipboard_clear()
    add_user(newusr,newpasswd,newtime)

def main():

    ipv6 = ""
    ipv4 = ""
    etherip = ""
    myip = ""

    # Wi-Fi IP
    ipv6_process = subprocess.run("powershell -encoded KABHAGUAdAAtAE4AZQB0AEkAUABBAGQAZAByAGUAcwBzACAALQBBAGQAZAByAGUAcwBzAEYAYQBtAGkAbAB5ACAASQBQAHYANgAgAHwAIABXAGgAZQByAGUALQBPAGIAagBlAGMAdAAgAHsAIAAkAF8ALgBQAHIAZQBmAGkAeABPAHIAaQBnAGkAbgAgAC0AZQBxACAAJwBSAG8AdQB0AGUAcgBBAGQAdgBlAHIAdABpAHMAZQBtAGUAbgB0ACcAIAAtAGEAbgBkACAAJABfAC4AUwB1AGYAZgBpAHgATwByAGkAZwBpAG4AIAAtAGUAcQAgACcAUgBhAG4AZABvAG0AJwAgAC0AYQBuAGQAIAAkAF8ALgBBAGQAZAByAGUAcwBzAFMAdABhAHQAZQAgAC0AZQBxACAAJwBQAHIAZQBmAGUAcgByAGUAZAAnACAAfQApAC4ASQBQAEEAZABkAHIAZQBzAHMA".split(),stdout=subprocess.PIPE)
    dirty_ipv6 = str(ipv6_process.stdout.decode())
    if dirty_ipv6.strip() != "":
        ipv6 = dirty_ipv6[:-2]
        myip = ipv6
    else:
        ipv4_process = subprocess.run("powershell -encoded KABHAGUAdAAtAE4AZQB0AEkAUABBAGQAZAByAGUAcwBzACAALQBBAGQAZAByAGUAcwBzAEYAYQBtAGkAbAB5ACAASQBQAHYANAAgAHwAIABXAGgAZQByAGUALQBPAGIAagBlAGMAdAAgAHsAIAAkAF8ALgBQAHIAZQBmAGkAeABPAHIAaQBnAGkAbgAgAC0AZQBxACAAJwBEAGgAYwBwACcAIAAtAGEAbgBkACAAJABfAC4AUwB1AGYAZgBpAHgATwByAGkAZwBpAG4AIAAtAGUAcQAgACcARABoAGMAcAAnAH0AKQAuAEkAUABBAGQAZAByAGUAcwBzAA==".split(),stdout=subprocess.PIPE)
        dirty_ipv4 = str(ipv4_process.stdout.decode())
        if dirty_ipv4 != "": 
            ipv4 = dirty_ipv4[:-2]
            myip = ipv4
    
    # Ethernet IP
    etherip_process = subprocess.run("powershell -encoded KABHAGUAdAAtAE4AZQB0AEkAUABBAGQAZAByAGUAcwBzACAALQBBAGQAZAByAGUAcwBzAEYAYQBtAGkAbAB5ACAASQBQAHYANAAgAHwAIABXAGgAZQByAGUALQBPAGIAagBlAGMAdAAgAHsAIAAkAF8ALgBQAHIAZQBmAGkAeABPAHIAaQBnAGkAbgAgAC0AZQBxACAAJwBNAGEAbgB1AGEAbAAnACAALQBhAG4AZAAgACQAXwAuAFMAdQBmAGYAaQB4AE8AcgBpAGcAaQBuACAALQBlAHEAIAAnAE0AYQBuAHUAYQBsACcAIAAtAGEAbgBkACAAJABfAC4ASQBuAHQAZQByAGYAYQBjAGUAQQBsAGkAYQBzACAALQBlAHEAIAAnAEUAdABoAGUAcgBuAGUAdAAnAH0AKQAuAEkAUABBAGQAZAByAGUAcwBzAA==".split(),stdout=subprocess.PIPE)
    dirty_etherip = str(etherip_process.stdout.decode())
    if dirty_etherip.strip() != "":
        etherip = dirty_etherip[:-2]
    
    use_wifi = True
    use_wifi = input("Enter 1 for Wi-Fi or 0 for Ethernet (default Wi-Fi):")
    if use_wifi != "":
        use_wifi = int(use_wifi)
    else:
        use_wifi = True

    myip = myip if use_wifi else etherip
    # print(myip)

    t = Tk()
    t.title("Remote Desktop Manager")
    t.geometry("1100x550")
    t.configure(bg="#2C3E50")
    # t.resizable(0,0)
    Label(t, bg="#34495E").place(anchor='center',width=5,relheight=1,relx=0.5,rely=0.55)
    Label(t, text="Welcome to Blockchain Remote Desktop Manager!", font="Helvetica 19 bold italic", fg="white", bg="#34495E", pady=10).place(anchor='center',relx=0.5, rely=0.05, relwidth=1)
    Label(t, text=f"Your IP: {myip}", font="Helvetica 11 bold",fg='white',bg="#34495E").place(anchor='center',relx=0.5,rely=0.975)
    Label(t, text="Client", font="Helvetica 15 underline bold",fg="white",bg="#2C3E50").place(anchor='center',relx=0.25,rely=0.165)
    
    ip = StringVar()
    usr = StringVar()
    passwd = StringVar()
    
    Label(t, text="Enter IPv4/IPv6 address:",font="Helvetica 11",fg="white",bg="#2C3E50").place(anchor='center',relx=0.25,rely=0.3)
    dip = Entry(t, textvariable=ip,font="Helvetica",bg="#ECF0F1",relief="solid",justify='center',insertwidth=5,width=30)
    dip.place(anchor='center',relx=0.25,rely=0.36)

    Label(t, text="Enter Username:",font="Helvetica 11",fg="white",bg="#2C3E50").place(anchor='center',relx=0.25,rely=0.48)
    dusr = Entry(t, textvariable=usr,font="Helvetica",bg="#ECF0F1",relief="solid", justify='center')
    dusr.place(anchor='center',relx=0.25,rely=0.54)

    Label(t, text="Enter Password:",font="Helvetica 11",fg="white",bg="#2C3E50").place(anchor='center',relx=0.25,rely=0.66)
    dpasswd = Entry(t, textvariable=passwd,font="Helvetica",bg="#ECF0F1",relief="solid", justify='center')
    dpasswd.place(anchor='center',relx=0.25,rely=0.72)
    
    button_style = {'fg':'white','bg':'#2980B9','font':('Helvetica',12,'bold')}
    Button(t, text="Connect", command=lambda: start_client(dip.get(),dusr,dpasswd), **button_style).place(anchor='center',relx=0.25,rely=0.9)

    Label(t, text="Host", font="Helvetica 15 underline bold",fg="white",bg="#2C3E50").place(anchor='center',relx=0.75,rely=0.165)
    Button(t, text="Allow Incoming Connections", command=start_host, **button_style).place(anchor='center',relx=0.75,rely=0.28)

    Label(t, bg="#34495E").place(anchor='center',relx=0.75,rely=0.34,relwidth=0.5,height=3)
    Label(t, text="New User Registration", font="Helvetica 14 bold underline",fg="lawngreen",bg="#34495E").place(anchor='center',relx=0.75,rely=0.42,height=50,width=280)
    
    newusr = StringVar()
    newpasswd = StringVar()
    newtime = StringVar()

    Label(t, text="Enter New Username:", font="Helvetica 11",fg="lightgreen",bg="#2C3E50").place(anchor='center',relx=0.75,rely=0.50)
    dnewusr = Entry(t, textvariable=newusr,font="Helvetica",bg="#ECF0F1",relief="solid", justify='center')
    dnewusr.place(anchor='center',relx=0.75,rely=0.56)

    Label(t, text="Enter New Password:", font="Helvetica 11",fg="lightgreen",bg="#2C3E50").place(anchor='center',relx=0.75,rely=0.64)
    dnewpasswd = Entry(t, textvariable=newpasswd,font="Helvetica",bg="#ECF0F1",relief="solid", justify='center')
    dnewpasswd.place(anchor='center',relx=0.75,rely=0.70)
    
    Label(t, text="Enter Time Limit (in minutes):", font="Helvetica 11",fg="lightgreen",bg="#2C3E50").place(anchor='center',relx=0.75,rely=0.78)
    dnewtime = Entry(t, textvariable=newtime,font="Helvetica",bg="#ECF0F1",relief="solid", justify='center')
    dnewtime.place(anchor='center',relx=0.75,rely=0.84)

    Button(t, text="Add", command=lambda: add_new_user(dnewusr,dnewpasswd,dnewtime), fg='white', bg="lime", font="Helvetica 12 bold").place(anchor='center',relx=0.75,rely=0.94)

    t.mainloop()

try:
    main()
except Exception as e:
    print(e)
    exit()