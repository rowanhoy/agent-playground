1. Open project as dev container
2. login to azure cli if not already and run the below to start the azure mcp server.
```bash
npx -y @azure/mcp@latest server start --transport sse
```
3. From a new terminal run the below to allow for log collection
```bash
docker run --rm --name jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 5778:5778 \
  -p 9411:9411 \
  jaegertracing/jaeger:2.6.0
```

The Jaeger UI should now be accessible on port 16686 to review telemetery

4. Copy the .env.example file into .env and fill in the required keys
5. Start the frontend and backend with either vscode debug "run all" or with the below without debugging.
```bash
cd webapp/frontend
pnpm run dev
```

The webapp will be accessible at http://localhost:5000
