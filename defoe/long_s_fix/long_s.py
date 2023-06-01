import subprocess
import re


def get_defoe_home():
    current_username = input(
        "What is your current username? [rosa_filgueira_vicente]\n"
    )

    if not current_username:
        current_username = "rosa_filgueira_vicente"

    return f"/home/{current_username}/defoe/"


# change this according to your path
defoe_path = get_defoe_home()
os_type = "sys-i386-64"
# Use the following value for os variable in case you are running this in a MAC
# os_type= "sys-i386-snow-leopard"


def longsfix_sentence(sentence):
    print("Original sentence: %s" % sentence)
    if "'" in sentence:
        sentence = sentence.replace("'", "'\\''")

    cmd = (
        "printf '%s' '"
        + sentence
        + "' | "
        + defoe_path
        + "defoe/long_s_fix/"
        + os_type
        + "/lxtransduce -l spelling="
        + defoe_path
        + "defoe/long_s_fix/f-to-s.lex "
        + defoe_path
        + "defoe/long_s_fix/fix-spelling.gr"
    )

    try:
        proc = subprocess.Popen(
            cmd.encode("utf-8"),
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()

        if "Error" in str(stderr):
            print("---Err: '{}'".format(stderr))
            stdout_value = sentence
        else:
            stdout_value = stdout

        fix_s = stdout_value.decode("utf-8").split("\n")[0]
    except:  # TODO: Change bare excepts to explicit
        fix_s = sentence
    if re.search("[aeiou]fs", fix_s):
        fix_final = re.sub("fs", "ss", fix_s)
    else:
        fix_final = fix_s

    print("Final sentence %s" % fix_final)
    return fix_final


sentence = "This a fentence test"
longsfix_sentence(sentence)
