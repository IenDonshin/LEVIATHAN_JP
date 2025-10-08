# Build the Leviathan (Power Transfer Game) in Japan

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
