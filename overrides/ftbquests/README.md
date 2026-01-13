FTB Quests import instructions

This folder contains FTB Quests import files used by the JMendes All-In-One pack. The files included are:
- quests.json — full FTB Quests export (ATM-style layout and icons). Replace sample quests with your final content.
- lootbags.json — loot bag definitions used by custom mechanics or rewards.
- secret_quests.json — hidden/secret quests that are discovered by players.

How to import
1. On a server using FTB Quests (or a client with singleplayer world): stop the server if running.
2. Copy these files into the world save or server config location where FTB Quests reads imports. Common locations:
   - server world save folder: world/data/ftbquests or world/ftbquests
   - some servers/configs use: config/ftbquests or mods/ftbquests/import
   If you're unsure, check your pack/server documentation for the correct import path.
3. Start the server/world. Use the FTB Quests editor (in-game) to open the import action and import quests.json.
4. Verify icons, triggers and rewards. Some custom triggers or mod items may require the server to have matching mods and versions installed.

Notes
- The provided quests.json is a skeleton/sample using an ATM-style layout. Replace or expand quests before public release.
- Keep backups of existing quest files before overwriting.
- If you encounter missing item/icon errors, ensure the mod that provides the item is present and loaded.

If you want me to convert a specific FTB Quests export into this layout, provide the export and I can adapt it for you.
