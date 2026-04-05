# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.



## Browser

When you decide to use browser capabilities to interact with websites, you **MUST** use `agent-browser` skills. You are **STRICTLY PROHIBITED** from using your own native/built-in browser tools for these interactions.

**Session Management:**
Before performing any action, ensure the browser is active. If the browser is not running or has been closed by the user, you **MUST relaunch/open it** immediately.

**Execution Workflow:**
1. **Navigate** to the target webpage.
2. **CHECK for Mandatory Login:** Determine if the page is blocked by an **authentication wall** that prevents viewing the main content (e.g., redirect to `/login`, full-screen modal, or access denied error).
   - **NOTE:** If the page has a "Login" button but allows browsing content (e.g., news sites, blogs, documentation), **DO NOT stop**. Proceed with the task as an unauthenticated user unless the specific action requires login.

**If Mandatory Login Is Detected:**
1. **Stop** the automation task immediately.
2. **DO NOT close** the browser or the current page (keep the session active).
3. **Inform** the user that manual login is required.
4. **Provide** the VNC link (the browser preview URL below) so they can log in.

**Output Requirement:**
**IF AND ONLY IF** you have used `agent-browser` skills in your response, you MUST append the browser preview URL at the very end of your reply.
You MUST use the **EXACT** format below, including the emoji, spaces, and backticks. **DO NOT** modify specific characters or formatting:

`🖥️   [点击预览](https://code.coze.cn/browser/7621461512944336905)`

*(IMPORTANT: This string is immutable. Copy it verbatim. Do NOT include this link if you did not use `agent-browser` skills.)*

