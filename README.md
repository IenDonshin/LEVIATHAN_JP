# Build the Leviathan (Power Transfer Game) in Japan

## Project Overview

This is an otree project for the public goods game with punishment. There are three treatments in this experiment: 

1.fixed: Participants' power to punish is fixed. 

2.transfer_free: Participants can transfer their power to punish to others at no cost.

3.transfer_cost: Participants must pay a cost to transfer their power to punish to others.


## How to Run the Project

For now, development and testing are being conducted on the local network.

1. Clone the repository to the PC which you choose as the server.

2. Start the project from the command line:

```    
otree devserver 0.0.0.0:8000
```

3. Access the experiment by links:

    - Make sure the participant's device is connected to the same local network (LAN) as the server.


## How to Test the Project Automaticly

Test the project from the command lines：

``` 
otree test pggp_fixed
```

``` 
otree test pggp_transfer_free
```

```
otree test pggp_transfer_cost
```
These command lines can only submit fixed values (contribution, punishment and power transfer). After modifying the code, use these command lines to test whether the experimental process can be completed smoothly.

## How to Go Directly to a Specific Round

Click on "Sessions", then "Create new session". Next, go to "Configure session" and check the box for "use_browser_bot". Please note that it defaults to jumping to round 3, but this can be modified. To finish, click the blue "Create" button. After all participant pages for the session have been opened, each one will automatically navigate to the specific round.