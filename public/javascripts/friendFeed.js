const userImageElement = document.getElementById("userImage");
const userNameElement = document.getElementById("userName");
const trackNameElement = document.getElementById("trackName");
const artistNameElement = document.getElementById("artistName");
const contextNameElement = document.getElementById("contextName");
const timestampElement = document.getElementById("timestamp");
const fetchButtonElement = document.getElementById("fetchButton");
const errorElement = document.getElementById("error");

async function fetchFriendFeed() {
  errorElement.style.display = "none";
  fetchButtonElement.disabled = true;
  fetchButtonElement.innerHTML = "Please wait...";
  try {
    const response = await fetch("/api/getFriendFeed");
    if (!response.ok) {
      fetchButtonElement.disabled = false;
      fetchButtonElement.innerHTML = "Click to refresh.";
      errorElement.style.display = "block";
      errorElement.innerHTML = `HTTP error! status: ${response.status}`;
      throw new Error(`HTTP error! status: ${response.status}`);
    } else {
      fetchButtonElement.disabled = false;
      fetchButtonElement.innerHTML = "Click to refresh.";

      const friendFeedArray = await response.json();
      // 0
      const friendFeed = friendFeedArray[0];

      const user = friendFeed.user;
      const userName = user.name;
      const userImageUrl = user.imageUrl;

      const track = friendFeed.track;
      const trackName = track.name;

      const artist = track.artist;
      const artistName = artist.name;

      const context = track.context;
      const contextName = context.name;

      const timestamp = friendFeed.timestamp;

      function convertDate(timestamp) {
        const date = new Date(timestamp);
        const options = {
          //year: "numeric",
          //month: "numeric",
          //day: "numeric",
          //hour: "2-digit",
          minute: "2-digit",
          //second: "2-digit",
        };

        return date.toLocaleString("tr-TR", options);
      }

      function getTimeDifference(pastTimestamp) {
        const currentTimestamp = Date.now(); // Get current timestamp
        const differenceInMs = currentTimestamp - pastTimestamp; // Difference in milliseconds

        const differenceInSeconds = Math.floor(differenceInMs / 1000);
        const differenceInMinutes = Math.floor(differenceInSeconds / 60);
        const differenceInHours = Math.floor(differenceInMinutes / 60);
        const differenceInDays = Math.floor(differenceInHours / 24);

        if (differenceInDays > 0) {
          return `${differenceInDays} day(s) ago`;
        } else if (differenceInHours > 0) {
          return `${differenceInHours} hour(s) ago`;
        } else if (differenceInMinutes > 0) {
          return `${differenceInMinutes} minute(s) ago`;
        } else {
          return "Just now";
        }
      }

      userImageElement.src = userImageUrl;
      userNameElement.textContent = userName;
      trackNameElement.textContent = trackName;
      artistNameElement.textContent = artistName;
      contextNameElement.textContent = contextName;

      const differenceInMinutes = Math.floor(
        (Date.now() - timestamp) / (1000 * 60)
      );

      if (differenceInMinutes <= 10) {
        timestampElement.textContent = "Online";
      } else {
        timestampElement.textContent = getTimeDifference(timestamp);
      }
    }
  } catch (error) {
    console.error("Error fetching friend feed:", error);
  }
}
