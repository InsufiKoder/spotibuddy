var express = require("express");
var router = express.Router();

const { spawn } = require("child_process");
require("dotenv").config();

// Function to run the python scripts. Takes the script path and an array of arguments to pass to the script
const runPythonScript = (scriptPath, args = []) => {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn("python", [scriptPath, ...args]);
    let output = "";
    let errorOutput = "";

    //Collect the output and error output from the python script
    pythonProcess.stdout.on("data", (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on("data", (data) => {
      errorOutput += data.toString();
    });

    //Resolve the promise when the script exits
    pythonProcess.on("close", (code) => {
      if (code === 0) {
        resolve(output.trim());
      } else {
        reject(new Error(errorOutput || `Script exited with code ${code}`));
      }
    });
  });
};

router.get("/", async function (req, res, next) {
  try {
    // Function to fetch the token from the python script
    const getToken = async (retryCount = 0) => {
      try {
        const output = await runPythonScript("python/getToken.py", [
          process.env.SP_DC,
        ]);
        const lines = output.split("\n");
        return { clientId: lines[0], token: lines[1] };
      } catch (err) {
        // Retry fetching the token up to 3 times
        if (retryCount < 3) {
          console.log(`Retrying to fetch token... Attempt ${retryCount + 1}`);
          return getToken(retryCount + 1);
        } else {
          // If it fails to fetch the token after 3 attempts, throw an error
          throw new Error("Failed to fetch token after 3 attempts");
        }
      }
    };

    // Function to fetch the friend feed from the python script
    const fetchFriendFeed = async (clientId, token, retryCount = 0) => {
      try {
        const output = await runPythonScript("python/getFriendFeed.py", [
          clientId,
          token,
          process.env.SP_DC,
        ]);

        // Replace single quotes with double quotes and parse the JSON
        let friendFeedOutput = output
          .replace(/([{,])\s*'([^']+?)'\s*:/g, '$1 "$2":')
          .replace(/:\s*'([^']+?)'/g, ': "$1"');

        let friendFeedJson = JSON.parse(friendFeedOutput);

        // Parse the user and track objects in the JSON
        friendFeedJson = friendFeedJson.map((item) => {
          return {
            ...item,
            user:
              typeof item.user === "string" ? JSON.parse(item.user) : item.user,
            track:
              typeof item.track === "string"
                ? JSON.parse(item.track)
                : item.track,
          };
        });

        res.json(friendFeedJson);
      } catch (err) {
        // Retry fetching the friend feed up to 3 times
        if (retryCount < 3) {
          console.log(
            `Retrying to fetch friend feed... Attempt ${retryCount + 1}`
          );

          // Refresh the token and try again
          const { clientId, token } = await getToken();
          return fetchFriendFeed(clientId, token, retryCount + 1);
        } else {
          // If it fails to fetch the friend feed after 3 attempts, throw an error
          console.error("Error fetching friend feed:", err);
          res
            .status(500)
            .send(
              "Terminating: Failed to fetch friend feed after token refresh."
            );
        }
      }
    };

    const { clientId, token } = await getToken();
    await fetchFriendFeed(clientId, token);
  } catch (err) {
    console.error("Error:", err);
    res.status(500).send("Error executing scripts");
  }
});

module.exports = router;
