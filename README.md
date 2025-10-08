# Build the Leviathan (Power Transfer Game) in Japan

## about the Project

This is an otree project for the public goods game with punishment. There are three treatments in this experiment: 

1.fixed: The participant's power to punish is fixed. 

2.transfer_free: Participants can transfer their power to punish to others at no cost.

3.transfer_cost: Participants must pay a cost to transfer their power to punish to others.


## How to Run the Project

1. Clone the repository to your local machine.

2. Start the project from the command line:

```    
otree devserver 0.0.0.0:8000
```

3. Access the experiment:

    - Make sure your device is connected to the same local network (LAN) as the PC running the project.

    - Open a browser on that device and enter the IP address of the PC running the project using the http protocol.

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

