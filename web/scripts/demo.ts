import { KVClient } from "../client";

async function demo() {
  try {
    const client = await KVClient.connect("127.0.0.1", 9000);
    await client.set(Buffer.from("city"), Buffer.from("salford"));
    console.log((await client.get(Buffer.from("city")))?.toString());
    client.close();
  } catch (e) {
    console.log("failed:", (e as Error).message);
  }
}
demo();