# SHIELD
CTF attack and defence traffic analyzer and automatic attack script generator

## Example Client - Server communication via gRPC
A short and easy introduction of flaghunting. Click through the example MessageBoard and try to get the hidden flag!

### Installation
As prerequisites you will need python and poetry, thats it!
Just make sure to add the poetry path to your path variables if necessary.

Now clone this repository into a directory of your choice, enter it and run the following three commands inside a powershell:
1. `.\build.ps1` to setup python, all requirements and the virtual environment.
2. `.\runServer.ps1` to start the server in this console.
3. `.\runClient.ps1` in another console to actually start the GUI.

### Goal
Now you should be prompted with the main menu of the program.
When you click on "Check Flag", you will see your hacker target.
But this Message Board is very secure and you will need a password to log in!

So first of all, make yourself comfortable with all the different functionalities in this demo project.
After playing around a little bit, find the hidden flag in the targets messages.
Good luck!
