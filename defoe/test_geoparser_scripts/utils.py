def get_defoe_home():
    current_username = input("What is your current username? [rosa_filgueira_vicente]")

    if not current_username:
        current_username = "rosa_filgueira_vicente"

    return f"/home/{current_username}/defoe/"
