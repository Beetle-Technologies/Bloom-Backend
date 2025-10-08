# Development Setup

To set up the development environment, follow these steps:

1. **Clone the Repository**  

   ```bash
   git clone https://github.com/Beetle-Technologies/Bloom-Backend.git

   cd Bloom-Backend
   ```

2. Make sureyou have Docker and Docker Compose installed on your machine. You can download them from [Docker's official website](https://www.docker.com/get-started).

3. **Create a `.env` File**  
   Copy the `.env.example` file to a new file named `.env`:

   ```bash
   cp .env.example .env
   ```

   Update the `.env` file with your local configuration.


4. **Build and Start the Containers**  
   Use Docker Compose to build and start the development environment:

   ```bash
   docker compose up
   ```

5. **Access the Application**
    Once the containers are up and running, you can access the application in your web browser at `http://localhost:3000/docs`.
