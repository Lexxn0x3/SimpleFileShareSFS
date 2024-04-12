# 🔄 SFS: SimpleFileShare

Welcome to **SFS** 🚀! This project is about making folder synchronization across the network between two computers possible. Whether you're working on a project with files scattered across different machines, or simply want to keep your documents in sync between your desktop and laptop, SyncMe has got you covered.

## Features 🌟

- **Auto-discovery** 🔍: No need to fumble around with IP addresses. SyncMe automatically discovers another instance running on the same network.
- **Easy synchronization** 🔄: With just a few simple steps, your folders are synced, ensuring you have the latest files across all your devices.
- **Efficient** 💡: Only changes since the last sync are transferred, saving time and bandwidth.
- **Cross-platform** 💻: Works across different operating systems, making it versatile for any setup.

# 🚀 Getting Started with Network Folder Sync 🚀

## 📦 What You Need

Before we start, make sure you have:

- Two computers connected to the same network.
- Python 3.x installed on both computers (because we're all about that code life!).
- Libraries tqdm and argparse


## 💾 Installation

1. Download the Network Folder Sync script to both computers. You can clone it from our repository or download it directly from our release page.
2. Install libraries
   ```bash
   pip install tqdm argparse
   ```
4. Navigate to the downloaded script's directory in your terminal or command prompt.

   ```bash
   cd path/to/network-folder-sync
   ```

## 🔍 Behind the Scenes

Here's a little peek at what's happening under the hood:

- **Auto-Discovery:** The script shouts into the network void, looking for another instance of itself. When it finds one, they shake hands (digitally, of course) and agree to sync up.

- **Secure Syncing:** Using the power of Python and some networking voodoo, your files are transferred securely between computers. No need to worry about sneaky eavesdroppers.

- **Smart Syncing:** Only files that are new or have been updated get transferred. No unnecessary data usage here!

## 🛠 Troubleshooting

Encountered a hiccup? Here are a few tips:

- Make sure both computers are connected to the same network.
- Check if Python is correctly installed on both machines by running `python --version`.
- If the auto-discovery isn't working, try restarting the script or your computers (the classic turn-it-off-and-on-again trick).
## How It Works 🛠

1. **Discovery**: One instance broadcasts a discovery message. When another instance receives this message, it responds, making the two instances aware of each other.
2. **TCP Connection**: A TCP connection is established between the two for secure and reliable data transfer.
3. **File Transfer**: Files are compared, and only those that are new or have been updated are transferred over the network.

## Contributions 🤝

Feel free to fork the project, open issues, and submit pull requests. Whether it's adding new features, fixing bugs, or improving documentation, all contributions are welcome!

## License 📄

This project is open-source and available under the GPL-2.0 License.

---

💡 **Tip**: Keep an eye on the console output for the status of the sync process. Happy syncing!
