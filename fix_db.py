def add_user(user_id, username, first_name, referrer=None):
    # Ensure values are not None (SQLite doesn't like None for string columns)
    if username is None:
        username = ""
    if first_name is None:
        first_name = ""
    
    c = get_cursor()
    try:
        c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
        if not c.fetchone():
            ref_code = f"FLX{user_id}{random.randint(100,999)}"
            c.execute(
                "INSERT INTO users (user_id, username, first_name, balance, referral_code, referred_by) VALUES (?,?,?,2,?,?)",
                (user_id, username, first_name, ref_code, referrer)
            )
            conn.commit()
            if referrer and referrer != user_id:
                # Give bonus
                c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (REFERRAL_BONUS, referrer))
                c.execute("INSERT INTO referrals (referrer_id, referred_id, bonus) VALUES (?,?,?)",
                          (referrer, user_id, REFERRAL_BONUS))
                conn.commit()
                try:
                    safe_send_message(referrer, f"🎉 *Referral Bonus!*\n\nSomeone joined using your link. You got ₹{REFERRAL_BONUS} added to your balance.")
                except:
                    pass
    except Exception as e:
        print(f"Add user error: {e}")
        conn.rollback()
    finally:
        close_cursor(c)