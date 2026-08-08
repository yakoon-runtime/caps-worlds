# Luma

*A spatial memory system built on Yakoon.*

Luma helps you think in *places* instead of folders.

Most knowledge systems organize information in trees, tags or search
indexes.

Humans rarely remember that way.

We remember *places*.

A childhood bedroom. A bookshelf. A desk. A drawer. A pocket. A box.

Spatial memory is one of the strongest memory systems we possess.

Luma explores a simple question:

> **What if knowledge were stored the same way we naturally remember it?**

Instead of folders, Luma offers *worlds*. Instead of documents, *boxes*.
Instead of hyperlinks, *exits*. Instead of attaching notes to objects,
notes exist independently and become meaningful only when *placed*
somewhere.

## The Model

```
World
 ├── Box (Office)
 │    ├── Endpoint "Door" ── Connection ──► Endpoint "Door" ── Box (Kitchen)
 │    ├── Box (Desk)
 │    │      └── Box (Drawer)
 │    │             └── Box (Envelope)
 │    └── Note
 │
 └── Box (Garden)
```

**Everything is a Box.**  
**Everything has a place.**  
**Ideas exist before places.**

A room is modeled in three parts. A **Box** is a place. A **Connection**
is a topological link between two boxes — the path itself, bidirectionally
navigable by default. An **Endpoint** is the local view of a connection as
seen from one box: its own name, description and orientation. The same
connection looks different from each side — a *red door* from one room, a
*locked hall entrance* from the other.

Worlds are not isolated. A connection may lead from a box in one world into
a box of another world — a wardrobe that opens into a different knowledge
area. Moving through it switches the current world; the world you leave
stays where it was, connected and reachable again.

## A Walkthrough

```bash
world/add NLP

box/add Office --world NLP

enter NLP

place Desk

go Desk

note/add Time

note/put Time
```

Not all commands — just the flow of thought.

## What Luma is not

- Not a wiki.
- Not a note-taking app.
- Not a MUD.
- Not a file system.

Luma borrows ideas from all of them but follows a different model:
**Luma separates creating ideas from placing them.**

## Built on Yakoon

Luma is implemented as a Yakoon Space. It demonstrates how spatial
knowledge, navigation and process-oriented runtime services can be
combined into a persistent thinking environment.
