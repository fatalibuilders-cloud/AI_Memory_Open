# Getting it onto your friends' phones

Three ways, no Play Store involved. They are listed easiest-first, and the
first one is almost certainly the one you want.

---

## 1. Send a link (best)

Once GitHub Pages is switched on (see the bottom of this page), the game
lives at a URL. You send that URL in the family WhatsApp group; everyone
taps it and plays.

Why this beats everything else:

- **Android and iPhone both.** The APK is Android-only. Half your relatives
  are not.
- **No scary warnings.** No "install from unknown sources", no "this file
  may harm your device".
- **It becomes an app.** Chrome offers *Install app*; on iPhone it is
  Share → *Add to Home Screen*. After that it has the lion icon, opens
  full-screen with no address bar, and looks like any other app.
- **It works offline.** The first visit downloads about 200 KB. After that
  the phone keeps it, and it opens on a matatu with no signal and no data
  left. That is the service worker's whole job.
- **You can fix things.** Push a change and everyone gets it on next launch.
  With a file or an APK you would be asking eleven people to re-download.

**The game carries its own address.** On the home screen there is
**📣 Send the game to a friend** — it opens a card with the link, a **Copy
link** button and a **Share…** button that hands straight to WhatsApp. That
button exists because once the game is installed to a home screen there is
no address bar to copy the link from, which makes an installed copy
impossible to pass on. Now every player can pass it on, which is also the
cheapest growth this game will ever get.

The downloaded file and the APK show the same button, and it sends the web
address — so even someone you handed a file to can invite the next person.

**What to actually send them:**

> Try the game I built 🦁
> https://fatalibuilders-cloud.github.io/AI_Memory_Open/
> Open it in Chrome, then tap the menu and "Install app" so it stays on
> your phone. Works without data after that.

---

## 2. Send the file

`node build.mjs` makes `nairobi-wild.html` — one file, about 170 KB, the
whole game inside it. Send it as a WhatsApp document.

This works, and it needs nothing from you but the file. It is clumsier at
their end: the file lands in **Downloads**, and they have to tap it and
choose **Chrome** to open it. Some people will get stuck there. It also
cannot be added to the home screen the way the link can, and when you
improve the game you have to send the file round again.

Worth it for one person with no data to spare, or if you want to hand the
game to someone sitting next to you over Bluetooth.

---

## 3. Send the debug APK

A real Android app: its own icon, its own entry in the app drawer, no
browser anywhere. Download `nairobi-wild-apk-debug` from **Actions → Nairobi
Wild — Android → Artifacts**, unzip it, and share the `.apk`.

The costs are real:

- **Android only.**
- Android will warn them, twice, before installing something that did not
  come from the Play Store. They must allow "install unknown apps" for
  whichever app they are opening it from. Expect to talk at least one person
  through this.
- Some messengers refuse to forward `.apk` files. A download link is safer.
- It is a *debug* build — signed with Android's throwaway key, not yours.
  Perfectly fine for testing. It cannot go to Play, and a later Play version
  will not install over it.

Best for the handful of people who will actually give you feedback and want
the real thing on their phone.

---

## What to ask them

They are not testers, so do not send a form. Ask two questions:

1. **Did the animals make their own sounds?** This has been wrong three
   times and no machine can check it. If they say "beeps", say so here.
2. **Where did you stop playing, and why?** "Got bored at Kisumu" and "level
   9 was impossible" are different problems and both are worth knowing.

And watch one person play without helping them. That is worth more than ten
replies.

---

## Switching the link on (one time, 20 seconds)

1. GitHub → the repository → **Settings**
2. **Pages** in the left sidebar
3. **Build and deployment → Source → GitHub Actions**

That is all. The next push publishes, and the run's summary prints the URL.
Nothing is published before you do this, and the page is public afterwards —
anyone with the link can play, which is the point, but it is not a secret
link.

To take it down again: same screen, **Unpublish site**.
