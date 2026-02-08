import discid
import urllib.request

disc = discid.read("/dev/cdrom")
disc_id = disc.freedb_id

# Now read the full record
read_url = (
        f"http://gnudb.gnudb.org/~cddb/cddb.cgi"
        f"?cmd=cddb+read+data+{disc_id}"
        f"&hello=user+hostname+cdrip+0.1&proto=6"
    )
print(read_url)

req = urllib.request.Request(read_url)
with urllib.request.urlopen(req) as response:
    result = response.read().decode("utf-8")
    print("Full record:")
    print(result)

# http://gnudb.gnudb.org/~cddb/cddb.cgi?cmd=cddb+read+data+cd0e9c8d&hello=user+hostname+cdrip+0.1&proto=6
# http://gnudb.gnudb.org/~cddb/cddb.cgi?cmd=cddb+read+data+{'cd0e9c0f'}&hello=user+hostname+cdrip+0.1&proto=6