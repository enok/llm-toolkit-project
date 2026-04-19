---
title: SQL Injection Prevention — Parameterized Queries Only
impact: CRITICAL
impactDescription: SQL injection is the #1 web vulnerability, enables data theft and destruction
tags: security, injection, sql, parameterized-queries, owasp
---

## SQL Injection Prevention

Never concatenate user input into SQL queries. Always use parameterized queries or ORM query builders.

**Incorrect (string concatenation — trivially exploitable):**

```java
String sql = "SELECT * FROM users WHERE name = '" + name + "'";
// Input: name = "'; DROP TABLE users; --"
```

```python
cursor.execute(f"SELECT * FROM orders WHERE id = '{order_id}'")
```

**Correct (parameterized queries):**

```java
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE name = ?");
stmt.setString(1, name);
```

```python
cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
```

```typescript
const result = await db.query("SELECT * FROM users WHERE email = $1", [email]);
```

- Applies to SQL, NoSQL (MongoDB), LDAP, and any query language
- ORM query builders (Hibernate, SQLAlchemy, Prisma) are safe by default
- Never use string interpolation even for "internal" queries — inputs can be tainted
