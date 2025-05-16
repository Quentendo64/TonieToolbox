#!/usr/bin/python3
"""
Constants used throughout the TonieToolbox package
"""
SAMPLE_RATE_KHZ: int = 48
ONLY_CONVERT_FRAMEPACKING: int = -1
OTHER_PACKET_NEEDED: int = -2
DO_NOTHING: int = -3
TOO_MANY_SEGMENTS: int = -4
TIMESTAMP_DEDUCT: int = 0x50000000
OPUS_TAGS: list[bytearray] = [
    bytearray(
        b"\x4F\x70\x75\x73\x54\x61\x67\x73\x0D\x00\x00\x00\x4C\x61\x76\x66\x35\x38\x2E\x32\x30\x2E\x31\x30\x30\x03\x00\x00\x00\x26\x00\x00\x00\x65\x6E\x63\x6F\x64\x65\x72\x3D\x6F\x70\x75\x73\x65\x6E\x63\x20\x66\x72\x6F\x6D\x20\x6F\x70\x75\x73\x2D\x74\x6F\x6F\x6C\x73\x20\x30\x2E\x31\x2E\x31\x30\x2A\x00\x00\x00\x65\x6E\x63\x6F\x64\x65\x72\x5F\x6F\x70\x74\x69\x6F\x6E\x73\x3D\x2D\x2D\x71\x75\x69\x65\x74\x20\x2D\x2D\x62\x69\x74\x72\x61\x74\x65\x20\x39\x36\x20\x2D\x2D\x76\x62\x72\x3B\x01\x00\x00\x70\x61\x64\x3D\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30"),
    bytearray(
        b"\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30")
]

# Mapping of language tags to ISO codes
LANGUAGE_MAPPING: dict[str, str] = {
    # Common language names to ISO codes
    'deutsch': 'de-de',
    'german': 'de-de',
    'english': 'en-us',
    'englisch': 'en-us',
    'français': 'fr-fr',
    'french': 'fr-fr',
    'franzosisch': 'fr-fr',
    'italiano': 'it-it',
    'italian': 'it-it',
    'italienisch': 'it-it',
    'español': 'es-es',
    'spanish': 'es-es',
    'spanisch': 'es-es',
    # Two-letter codes
    'de': 'de-de',
    'en': 'en-us',
    'fr': 'fr-fr',
    'it': 'it-it',
    'es': 'es-es',
}

# Mapping of genre tags to tonie categories
GENRE_MAPPING: dict[str, str] = {
    # Standard Tonie category names from tonies.json
    'hörspiel': 'Hörspiele & Hörbücher',
    'hörbuch': 'Hörspiele & Hörbücher',
    'hörbücher': 'Hörspiele & Hörbücher',
    'hörspiele': 'Hörspiele & Hörbücher',
    'audiobook': 'Hörspiele & Hörbücher',
    'audio book': 'Hörspiele & Hörbücher',
    'audio play': 'Hörspiele & Hörbücher',
    'audio-play': 'Hörspiele & Hörbücher',
    'audiospiel': 'Hörspiele & Hörbücher',
    'geschichte': 'Hörspiele & Hörbücher',
    'geschichten': 'Hörspiele & Hörbücher',
    'erzählung': 'Hörspiele & Hörbücher',
    
    # Music related genres
    'musik': 'music',
    'lieder': 'music',
    'songs': 'music',
    'music': 'music',
    'lied': 'music',
    'song': 'music',
    
    # More specific categories
    'kinder': 'Hörspiele & Hörbücher',
    'children': 'Hörspiele & Hörbücher',
    'märchen': 'Hörspiele & Hörbücher',
    'fairy tale': 'Hörspiele & Hörbücher',
    'märche': 'Hörspiele & Hörbücher',
    
    'wissen': 'Wissen & Hörmagazine',
    'knowledge': 'Wissen & Hörmagazine',
    'sachbuch': 'Wissen & Hörmagazine',
    'learning': 'Wissen & Hörmagazine',
    'educational': 'Wissen & Hörmagazine',
    'bildung': 'Wissen & Hörmagazine',
    'information': 'Wissen & Hörmagazine',
    
    'schlaf': 'Schlaflieder & Entspannung',
    'sleep': 'Schlaflieder & Entspannung',
    'meditation': 'Schlaflieder & Entspannung',
    'entspannung': 'Schlaflieder & Entspannung',
    'relaxation': 'Schlaflieder & Entspannung',
    'schlaflied': 'Schlaflieder & Entspannung',
    'einschlafhilfe': 'Schlaflieder & Entspannung',
    
    # Default to standard format for custom
    'custom': 'Hörspiele & Hörbücher',
}

    # Supported file extensions for audio files
SUPPORTED_EXTENSIONS = [
        '.wav', '.mp3', '.aac', '.m4a', '.flac', '.ogg', '.opus',
        '.ape', '.wma', '.aiff', '.mp2', '.mp4', '.webm', '.mka'
    ]

UTI_MAPPINGS = {
            'mp3': 'public.mp3',
            'wav': 'public.wav',
            'flac': 'org.xiph.flac',
            'ogg': 'org.xiph.ogg',
            'opus': 'public.opus',
            'aac': 'public.aac-audio',
            'm4a': 'public.m4a-audio',
            'wma': 'com.microsoft.windows-media-wma',
            'aiff': 'public.aiff-audio',
            'mp2': 'public.mp2',
            'mp4': 'public.mpeg-4-audio',
            'mka': 'public.audio',
            'webm': 'public.webm-audio',
            'ape': 'public.audio',
            'taf': 'public.audio'
        }

ARTWORK_NAMES = [
        'cover', 'folder', 'album', 'front', 'artwork', 'image', 
        'albumart', 'albumartwork', 'booklet'
    ]
ARTWORK_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']


TAG_VALUE_REPLACEMENTS = {
    "Die drei ???": "Die drei Fragezeichen",
    "Die Drei ???": "Die drei Fragezeichen",
    "DIE DREI ???": "Die drei Fragezeichen",
    "Die drei !!!": "Die drei Ausrufezeichen",
    "Die Drei !!!": "Die drei Ausrufezeichen",
    "DIE DREI !!!": "Die drei Ausrufezeichen",
    "TKKG™": "TKKG",
    "Die drei ??? Kids": "Die drei Fragezeichen Kids",
    "Die Drei ??? Kids": "Die drei Fragezeichen Kids",
    "Bibi & Tina": "Bibi und Tina",
    "Benjamin Blümchen™": "Benjamin Blümchen",
    "???": "Fragezeichen",
    "!!!": "Ausrufezeichen",
}

TAG_MAPPINGS = {
    # ID3 (MP3) tags
    'TIT2': 'title',
    'TALB': 'album',
    'TPE1': 'artist',
    'TPE2': 'albumartist',
    'TCOM': 'composer',
    'TRCK': 'tracknumber',
    'TPOS': 'discnumber',
    'TDRC': 'date',
    'TCON': 'genre',
    'TPUB': 'publisher',
    'TCOP': 'copyright',
    'COMM': 'comment',
    
    # Vorbis tags (FLAC, OGG)
    'title': 'title',
    'album': 'album',
    'artist': 'artist',
    'albumartist': 'albumartist',
    'composer': 'composer',
    'tracknumber': 'tracknumber',
    'discnumber': 'discnumber',
    'date': 'date',
    'genre': 'genre',
    'publisher': 'publisher',
    'copyright': 'copyright',
    'comment': 'comment',
    
    # MP4 (M4A, AAC) tags
    '©nam': 'title',
    '©alb': 'album',
    '©ART': 'artist',
    'aART': 'albumartist',
    '©wrt': 'composer',
    'trkn': 'tracknumber',
    'disk': 'discnumber',
    '©day': 'date',
    '©gen': 'genre',
    '©pub': 'publisher',
    'cprt': 'copyright',
    '©cmt': 'comment',
    
    # Additional tags some files might have
    'album_artist': 'albumartist',
    'track': 'tracknumber',
    'track_number': 'tracknumber',
    'disc': 'discnumber',
    'disc_number': 'discnumber',
    'year': 'date',
    'albuminterpret': 'albumartist',  # German tag name
    'interpret': 'artist',            # German tag name

}

CONFIG_TEMPLATE = {
    "metadata": {
        "description": "TonieToolbox configuration",
        "config_version": "1.0"     
    },
    "log_level": "silent", # Options: trace, debug, info, warning, error, critical, silent
    "log_to_file": False, # True if you want to log to a file ~\.tonietoolbox\logs
    "upload": {
        "url": [""], # https://teddycloud.example.com        
        "ignore_ssl_verify": False, # True if you want to ignore SSL certificate verification
        "username": "", # Basic Auth username
        "password": "", # Basic Auth password
        "client_cert_path": "", # Path to client certificate file
        "client_cert_key_path": "" # Path to client certificate key file
    }
}

ICON_BASE64="AAABAAEAAAAAAAEAIACkSwAAFgAAAIlQTkcNChoKAAAADUlIRFIAAAEAAAABAAgGAAAAXHKoZgAAAAFvck5UAc+id5oAAEteSURBVHja7V0HeFRV076Q3U0IXQQbVkqyJSQQQu9NekiHVHqHhGxJoUWaqAgqCqKiIoqICCoiKqAU6aKf7dPf3hVEUOlIdv6Zs/fGkC/knt1ka848z/tsSEKy2T3znukjSUIqLTqDVQrWWyQtPjIY8yRtuEWnMVivQ8Tg57IQ8xBrETsRnyB+RvyFuIgAhB1xHnES8T3iA8RbiKfk/0s/o6NWb7lJZ7DUrkm/Q/59+DukGs3NUlCYRbwZQoR4QrSGXMR0hEPxa5qYQtZDRCMmIVYjjiB+RZyRFRxchF3+GccQHyNeRMxFDEXcjgRQS2eylRBCUFiupAk3izdJiJCqV3yLpDHmyspGSmcJwY+jEHnyjU1KerkSyu4MiBS+RmxE5Gj11raIujoHGaFlYpNubD1HqoXWghAhQipj5httUjDdsvioM6CC6a0NUcniEM/L5rzdQ0pfkZVA5PM6kYHGYDEGG/K0+DwdboLejBAughAhzklEvlRbPwMVv8S/J8VPQ+yQb2DwQRQjvkM8iRiMJNCAiItiBTUjzFKQSRCBECGqojGSb29jQT6tyRrClMlgfQNxzkcVvzz8LbsmoykoGdLS4R7U1BcgIQjXQIiQ/5Xm06RgOcoeGmam29+AHz+GOOVHil8WlG3Yh5iAFsF1wRTH0FM8w8ziGkKECEEJIj+5xXQloh4ip98+9mPFL4tLiL3MjdGb67G/U08kVyDefCHVW7RoEmv0eSx6jrdkU1SOhxCnq1oJNWUQJKPs591MBOTGbEZ0CwrPCaKMhkY/FV8DkT4UUh39fTz4GjSFdcYZdPO3lv3mKlF2Uu6aehvUQOjw47omCzSKMMP1rXLhRsRNkbnQFHEjonErMzTEr9U2Wtj/p/9D/zdI7zZioDqFRYibtYb8kloCIUKqz81vtKIvbJFuarmKDn//ypr8GqbwjsdrUJlNbbIhofMksPUeC8sHjIT1QzPgrbhUOJQ0HN5PToGPUpLhU8QH+PHuhBGwZVgarB2SAUv7jwRzr7GQiP+3ddvpcAOSRSgSQ01GClVKBnbZLRikM9o0jACumyppwkVsQEjAm/2O3H6osbAGEkGyXIbrkiLRLU23/XWoqAM7ToH5fUfDG6joP6QmwunMeLCPHAYwKlbGsCsxssy/5e8rxs+fzoyDX9MS4AgSxtODMyGn5zjo2m4asyB0pcimCojgBOIujd5yLasdMNrY6yNESIDe/BZ2+9cyFZHyp8rmsNOKQwoYYrRCG7ylC/uMYbf4qYz4f5UaH0n5i10EI46R/xLDP/jx7+kJsD9xONx35yjo32EKIx2NTEKVJAOqYtxCbpBO73h9CEKEBJbPT4dbb5akZsvJ7E9xRfnptifFbx8zDR5E0/5bvOmLZUWtjMJzk4JMLkQ27yLpFPYew1wFh5tQaSL4FBGri7DWZFZSBJFAkTg4QvxfqHFGo7dKIZH5dLsNcNbsVwJ7LVrnwKJ+o5mJD/ItXewFKGRwGR+/x+fy2KAs6NNhKtQzVZoIjrEeA4OtFlkBwfh6UY2EECH+K3iAtREWhwXgaNX91NlbnyL0I7pOhPeSUpjSeUvxy4PiKpCL8PyQDOjfcQrUkYnARRI4i7hXo7c1oPSopj0SZ3i+OEdC/FNCIgpYYw8e6lvk3nyngny3RM5g0Xnm44/yHcW/mlVwIj0eVg/KZG6KTiYwF0jgH8TjOjbfwCLd3LRICtaLuIAQvwv6yT3zeksoPq5yVvmjoqfD63Fp7Na3j/Rd5S8vgPgdugZFfcfAbVEzSoqOXEgVrkd34CaKCdSJnC7pIkTRkBC/Uf48RgCSNEaSB3acc8bs79l+KkvDgZ8ofnmuAWUP3k0cDkM7TYZa6Ma4aA28iJZAU60eX8trc9GlEiXEQvxA6vbb5JjeY7S2w0P8jTMBvzs7TIH/Dk/2aZOfmwjwbziengAL+41mFYhBrsUGXsTX8Qad0SLVbj1Nkm4rEgdMiA/f/vqS2XkN8HGTMzd/7w5T4bMAUf6y1sDrw1Khfcx0V0qMyR1Yowm3NiJS1ZmEKyDEV6VHEevnr+EY6EGm/wVe5Y9pO52V6gaS8peNDRC5De8yidUzaJwvGHoYSaCuhg1KEWXDQnxQdC0cfe94WMN4U36k/HdEzYAd8akBqfzluQTUc0B1A0HOzxiYrTGZtaKJSIjvSVSO3OhjDcLDuYTX529gMsPjA7MCWvHLugRnMuPg3jtHsS5FJ0ngT8SokOYFjoGpop1YiK9InWazmP+PSt1BHtzJdain9hgPZ1Eh7NWEABSX4EJWHKxE4qMmIydJ4Ed8jfuwdmL9DCk0TDQQCfG2UMWfkc3y0/Hm/KlarmPMNPhqRJLfpvsqSwIUHHxyUKYrJHAQX+8WNEdRaiVcASFelmBTyXALuv1/4zH9qXd/w9D0gPf71UjgUtYweGJQFuswdJIE1uoMtnqOjIsICgrxorCBl2E06sr6AG/gb1S3CcwXto+svgRQmgQeHjCSTSfSOBcUNEthU2qw6UpiD4EQr0T+5ZJfPLgGeXOOqvLfHjWDTeipzrd/WRI4nxUH8/qOZs1PTpDAT4ju5ArUajlDHEYh3jD/bZLUgsZdW/N5NvbQ4c7rPRb+yRKKXzY78FdGPEzqMZ41EjnhCmzXGGzXK4tLhQjxiNBE36AWBYrv3wjxLs/t37x1Dnzo0YKfWCjOugp8kAR+Sk2EwZ0mOxMPoM1Es6UIa02NIw0rDqcQ90X7a7UqLJlmq2NjvvIp8j9c3oqjSgA0Y++SO29/UuzMoVCcMcTx73HJUDw5DYqnZkDxtEx8zHT8e3yK4+v0ffT9PkIIRIxUEdkqOtuZ3gFyBbrSe1IjQhCAkKoO8oWjid88p2Q9t05vrolm6u20AsvRtsoX+adR3DROq8pvf6b0qMij46E4eyQULyoA+5pHwf7Gy2A/uBfs//0I7F//H8D33wB88yXYP/sY7O8dAPtbW8C+dhUULyyA4ulZUDwqzifIgCyBF4ZmQGPngoKvaI2s/4JNYBIipPL+vSFXqqWfonT2STqDmXr7uyOWIf4rb77hHubZKWYa/JSWWHUEQMpKSps7FuyP3g/2t7c5lPzMaYDiYuASu93x/d9+BfZtm6H47plQPGG4V4lAKRSiuYPB/ARAfRdjQyJsUlC4qBAUUpkbHxVfFzaBNZ1ojJTjN9fHwxWP2CCPs3Zpfj8t6RjTbQL8KM/1c9mnJ+UclwTF86xgf30zwE/fA/xzCapEkAzsRw+C/aG7oXiiTAResgJ+SUuAfh2mODNi7APEHWytesRMcZCFOCtFkraVRW7ppRn+ljp4oBIQW6tiPbdizsZ3ngxfu1IBqCj+PbPBvu8dgD9Pgdvk/DmwH97ncA/IyvCCNUCWEjVJ0SYjJ4KCC4IjzDXZEtKmIjUohDeqb8qTarYqYKZ+kJ4aeiw98DBtdNe+vmFIAj/wWgKkfKSEdOPv3Qlw+m/wmJz8A+wb10LxlHR8Hp63BqhceG5fp1yB7xBRbLJwa7GSXAiPyS8vpNCFsyDfbYjFri7ucAZUDXgyI77iakC69cnHf+UFgD9OgFfk8mWwH9kPxYVTPW4JEEESUXZpN80ZV2B5zXCrhgUDxWhxIVdX/DwpqNl4R2TfZKE+81jEAU+sziYrgJZqLO43uvy0ICnamESwP3g3wBefOYJ13pZvv4TiRYWeJ4FRjqyAE6XCvzj6MmxSaJsicdCFlGPy422vCTezmf0ag432081HnPSE8peuC6BZedvLDgOhWz9nNNi3bnJE6H1JfvkJiu+d61ESsLOdhfGQ1nWiM7UBK9Bi0LDqwOjx4sALKXXzU5AvjObL5VP5aDgelpfksVOVu9X1FgcMFqd2/dFyT5qUYx8pK9WCPIBPP/SNW788+fVnFoj0ZEyACJL2IN7EHxCk4qBoZt2FiWnCQkpufivCsX9Orh47VDlTnpTeDLVMhXB9zDJo0+dlaNltDeiMeU65AqsGZgKMQRJYtQzg+K/g8/L9N1A8Z4bHSECpDZjWc5wzxUFLNYYZQVrRLiyEKb/RUSVWvwPN7mN7+j6vzG1Pjw1aLwBTz/UwIP59yMr8HSaOPQ+jRp5kn9MZbfxFQh1y4Oc1awDOngG/kU/+A8UzxnjMHSAr4GhyCuum5LQCqDtT76jeFNWB1dvspxlyRosU2oK17w50Zl5/WcUnxW4cfS/E9NsCySO+hfFjzsKkcRdh0tgLjAAmjbsAI7NOQBhaAtxWQKt8eGrjIfA3sb/5KhSPTfIYCVDAdEYvbiuAujPza0SaJV24GB1WbSVI7wj4sY09BmtvxFeumPr0SIrfacB2SEv/BZX9HFN2UvqyoM+npv8EN7Z7sMRaqNAKCDPD0Imr4e8zF/yLAahgaOX9HrUCjiSllKwd43jvjqC1dwPrETCJuoDqJ9FFkmTIk3RG1i/eBg/Cf1y59etFFjH/fkTaTw4FH1u+4pclgYHx/4E6reaoBgbpd9zQuQgOffi931kB1EdQbBnvERKgWMDFrDiY0mM8LwFQj0AaTW0KalUo9KG6SXBYjqRzdPHdhHjL2VtfZ7DBrR1XwtCkT2ACM/XVFb80xo85A616bcCfx5cZuPfxt/2PAMAO9lc3OKoVPWQF7EoYweYIcroCG/D7aoldAtXN9Fe6+EzszX/YWeWvHTELovu+yoJ7zir+v1bARUgY/hXUj5qnagXUQDcgfurTcPbcRf/jgBPHoXh2jkeah5S6gOQuk3irA38tSQkaRCyg2pj+NY0Wqa6BTezNcqaZh8zxhq0XQu+h+9kNzmPuq1kBhh7PqcYCgsItEHbnYvjup5Pgj0KFS560AjYMzWAbhjitgNmSIVsQQHWRWmHZiulPaaBPnFH+Jm3vgyGJH1dK6ctaAZQmpFoBtd99bfvZ8M7Br6pMKS9c/Af+uVzsGQY49gsU50/2SG2Ao104ETrEcPcIvItuWCOHG5AkFCSgU356Kwv66SJsOnQBHnFG+a9ruwTikj932eQvlwDQgsjIPMYyCBVZAXST1WqVB6srmQ6kAsIP/vsTzHv4LciwPgcT5rwIazYfgd9PurnGoLgY7Gsf89gMAXIFaJKwE2vFejOXsN1soSSBLJqWVmVuXx/eAR7s9m2zGIYlf1alyq9g3OgzEN59LQTpzarpwPkrtldCB+2w9uX3oGW/u5lLQXEFQmhkPgyZsBr+89nP7nUDPjoKxRNHeCQj4EgJDoemkdwpwcWSYVwNsVMwkE1/Uy5b0Y2oLffzcwX86kYWQf+49yvt71fkBnTo/4Z6ILClGbIXvoy3uGt9AG/u/Ryadp3HiORKgnOQS+/MlfDDL24cJPLXKSiem+vBYGAcJHSmYCBX1eVhRGORDQhggSckNh8e3+R+stmnejCCjfmsuGfC2HNuUX7CZCSAPrEHIcSUr5oJGFWwHi5euuy87p2+wIqJyip/aaBrBA8+s8e9bsDTKxxDSj0UDKQloyFGLgvgFKKnIxsg+gMC0/93LOkMxjf5ad7bv0XXp2D0qFNuu/0VC2Bw4scQGjGrwpoAIoARuWvh3AXnZ/y998mPcGOXogrjDPTzR+Y97xLBcLsBu96C4jEJHhsY8mlKMjRrze0GzA7S50nBggACT+SoPyGGZ6IPKX/D1gsgYfiXbvH7y1YFxqX8n2pVIN3eydlr4Ox55wngtXc+hQZtZ6oSQIZ1HcsOuI0A/u9Tx+4BD1UG0nr11K4ToQafG/CGzmipqxNuQAASgNEsSWEziQDm8Eb+Y/q95lbTvzQBxCPR1Gk1t0ICYBbADLQAXCCAve99A407zKmQAILwa5UJMnIXBXmoNNjhBsTCCn43gOYEhGvFoJAANP/JAtBbuNZ0sah/9D2stt/dt3+JBZD8ObMA1FwAZqK7cEOfOHWGBflqXCUGQFmB23stYK6CW+XMaSien+exdKCyTYhzevB5RAoRQMgd84TSBM7tL6f+9Kzbjyv417bvFtbR527lV2IAgxI+Uo8BtDTD1HmbWDrPFdm2+zNU8oXMlVAsAZYBCDdD/TaFsOzp3S7/bP4OwfNgX7bAo/UApzLindkhcM+1MVPFBqFAkmCTVaoZzkhgNo/v36D1XZA04muYMOYCwv0EQFmA3kMPsIyDWhZg9gPbKlUEtH3fF9Bv1Cpo2HYWm11QOzIfDAPugUee2+dScNFpuXQR7CuWeCwToCC/91heAngDUVekAwPM/Mcbr468xKPiYhu8DYeMXwNbt56DB5ZchOwp52H86PNuJQLeOgBK0y1f+26ldZCq/l5Ha4CU/rlXj8IX3/3uuRGD/1xio808SQAUB1g/JINtX+LoDfhaY7DdKgggoAiA3f7NEd+rEUBIRB489sIBdlbPngX4zwfFsPKRf4nAHQSgNARVVAlIpno9NNM3vvkh+LVcQgJ4dKlnCUBOB97CNyjkTySJXowAwkRzkP/7/y3MCgEMUFvTTVHwm7vNgw8/v7Ik9sJ5gPeOXIZ7Fl1kCluV1gDVF9CIsOvbLau4FwC/dn2nuXDk4x/8mwAuXnDsFvTgXkGKA5xIT4BufAtEihGTGQE0yRcK5Pf+/61mRwGQwTqDZ/RWn6xH4dTf58o9u3+csMP6dZdg+uSqIwEy/4dxZAAoSm8ceC/8fOwv/yaAs2fAvniWxwmAJgWN7z6Btx5gyTXNJtFOCKFA/i603CMoLLcmvqmqnX8UZMtesLnCSDhasLDr7ctgnVH5ACHd/hQA7Nj/Ta65gLGTnoTTZy/6NwFQP8DM6R7fJUhxgCV3juLtDnxJZ7KGUvZISCD4/0YbNf+8rFr3b7LBiuf2cUXTDx+6DPkW10iAFJ+QlfU7GyzCWoFVAoBEAPlLtoLfy08/QHH2SC+sEIuFl2LToT5fIPB9PDONtYIAAiYAeK3c7VXxpJ+2s2Drrv9yn+XDBy+DJYefBJjij7vAxoh1H7wbbmr/EISYCjiGglqhbusCeOH1//i9/tvfPwTFE4Z7ZYcg7Q24gW9W4M+IFiITEDgE0BTxrRoBULPMh070xJMlsGP7PzBtknpMgBSfloLQjd+0/XIINuaxrUF88wisUD96Jqzf+oH/E8CWFz2u/Eom4Ke0RDC2yebJBNAeyG6CAAKFAPSWMLUGIAqy3dF7odP98BcuAKx56tJVCYAUn9J81O13e6dVjhtfb3Fp6QgFAXfs/8KPU4AXwf7wPR4vAlICgbRuvU+HqTyZgJKSYDEiLDAsAOoA/F2NAKJi74djJ5zfuPvbr3aYNxddgdH/a/LTkpCoPpscnX4uKP6VRUoWaDVkiX/uB2BzAX+FYusEr1gARADnMuMgg78zMEdrtEnBMzYJJQoAAuimtt6blKtTykNw4tRZl8727l2XYerEfxWfVoLRsM8b2i27YntQpdeG4/Pskf4IfPX9Cf8z//fvcqwK87DylyYBa6+xvASwwFFCLlKBgUAAPeWJLxWWAPfIWAEn/zrn0uE+fdoOS++7yPoHqLCHWomr4ta/mjtAXYF+tSqMlQAv9Wj+v7xMwD13juIdDrIyKMIWpBGZgIAggF5qXYBEAD0rQQAkB/YVQ1rm99Csy5Os0aaqbv3ygoJ1ogrgoWf2+g8B0MpwD24LvhoBPD4oE2oZLXwbg4zWWoIAAoMAeqhbABbomvow/PHnWZfP+Gs7v4Dbuy2t5K1v4XYFWvS9G977+Ef/MP83rfOa4rtYC0Cr4uqJTEAAEACyeHu1EeCkUO0SHnBpPj5VDlKKrnmfRS4rP6UEaSho7YjZTsUDsmzPuzQizKPy289QXDDF49V/5dUC7IhPhWsjzDwEcABxjSCAwLAAWiGOqSmTfsA98Ovxv51zbS8Xw5MbD8GNXe5iP8MVf57mANzc4WHoNXQf2xjMUxmo/N9rYmbDqzs/8eW7H+ybn0cFjPMBC2AYHEoaDtfzFQPRxqjrBAEEAAHoDNY75HlvFXYC3tpjPnz9A390/TIq/6r1+6FJhzlOK7+i4NfF3A/dB+9hgUOqGSAMTvwIGkTN5yIBKhGOm/KU7wYEv/vaozMAedqCOceDfStvjRZK5PcWgNF6PT5+pnabUrvtYc4cO5n9T710GK7rONd55dc7lo3QdmGqE1B6A0rXEPQYslfeF2hR/VmN2s2GbXs+883W38cf8AnlVwjg2xGJcCvfXAAqB75dEEBguADXqA0DJUVqED0Ttrz9KdfZ3vjGh3CT02Y/fa8Nbumwgi0YnTDm7FWGjl6AsaP/BmPP57mCgmQFjJu1AS79c9m3jP9334biCSk+RQA/piZCi9Y5PATwq06ZECzEz10AvTWUWjx5ugFXrtuverD3HPmarep2RvnJnA+NmAlRvTdBZuYx1WnD9PWU1O/ZdGKe1eEUgPz8m2M+ZPp/5ROBv//dGpzA2w9wHBEpCMDfCUBvlYLDzDXwjXyQZx5Awf0Vt9zS/LzOw5eztKEzJj8tGaEg37jRp53aMtRpwFugM6hXrtUqNcrM6/LnSbAvne9Tyq8QwK9IAFFtp0OQej8AlY63FQTg5xJqGItWgI0sASsPASRnP3PVxRt/nT7P0m7OpPpYbCFmKQxN/MSluQEUI1BbHa4890ybe7f6cMn5c2BfsxKKR8X5lPIrBPAbEkDrttk8BHBC60gfCyXyZ6llylHiAImIc2qmdJthS+HYib/Laf21w5LVu9gYbY2e3+xv2uFhSBrxTaUWjET3fUU1I8BGhg26F3789U/vBv1eXAvFYxN9xu8vzwLgJIA/NAZrR0EAgZMJaC37daqZgPK67fYd/RZu67mA2+8nhb2l4wrmx9PcPyXS70j1XWSYrALH91zimhmoZAN2HvjSe8pP+f7xyT6p/Fe4ANFcLsAfOoOlkyCAwMkEUFHHRzy+9BMvHrzibFN58LDJT3L7/crNT6vFSIFpHsDokacgI/MYswaGoDvQb9hh6DF4D3QZuJPtBGh35+sM7e/cBp0H7mATg2hlOH3v0KRPoUnb+1StABbEfH6/55WfBn2+8DQUj/Nd5XeBAE6gBdBBEEAACG171RmttfDNfIEnDjC9zGBQmhMYymn6k5Je02YRm/zTP+4oU25D93Vwc4dHoFGbu1n+v3bELDYYhBqGlDLgIH0u2wvg2A1gYV+j76F1YXUj57KPeZ677d4tnlX+4785Fn3Qym8fVv4rXABOAkC0EwQQABIUgQTAuRqMtQWnPwIn/3R0BX71/e/QOvZ+p6L+tdFcrx81jxXykGlOSk2PRA6OW9y52gHerkIigJQc17YHO5/kR4L870dQvLBAVjDfVv7SBBAZzZUGpCxAtCCAQHABTFbFDYhFnFGfDXhXyZbcWcu2udbc46ZWYDXy6p218qp7Dao0zffqBijOGeXV/n5XCODntEQIb8NVCES9IxGCAAIrDnCH2nDQkvHg6/bB598ch5b97napyccboOcZHbcUjv9x2k0pvvNgP7IPiu+eCcWj433e5C+PAL5PTYTb+UqBfxGTgQOJAIwWAu0HeJWntHbEjLWQd99rbCGnPyi/QgCGgffCb7//XbWKf46WJB4B+/LFUDxxuF/d+mUJ4IvhSXBzJBcB/Ii4WRBAgEhwuFmqacojK2Amz8Sdxu3nwPWditwy0sttBCB3NJLlUvkRXv8AHPsF7G9vg+L7ilDxRzgU389u/bLtwB+lJMNNfN2AXyJuEAQQKJkAvaX0fMA/eUjAn5TfEXewQmirfFi98bDzCl9czNJ58ON3YN+z3dHFZ5uIpn6C3yt+aQI4zD8P4GNEE0EAARcHsNCb+p4/KbYzqIFuQMb4R+D80SMA337JRnHDqT8A/jzF9vJRAA9OngD45UeALz8D++F9YN/2MtifXgHFiwqhOHuUI6UXIEpflgD2JIyAxq24JgIdljdKCcUJFNHQm2mwUmPQkkAlAMpv66Nz4NtR6QDTMqA4Z7RjFj915hVOg+L8yVBsHufYzzcl3VG5RwqSMSQglb4sAbw2LA0a8o0E260xWhuK/YCBFAcwTCcLgDAA3+C/PayclxF/ydFlqkjcjliPeEzuVLy/FFYinkVsQ/xHnmZEz9fO4wY0NJlh67BUAMrNZykYWgqlPj8ycBW+vKGgzw3JgDp8Q0G3IOoICyCQxFhEPQE0JJTcgCNuVviLsrK/g3gAMQnRV6u3hmkcvmV9RIhGb9GE3j6jhnRtpiQ1TJekOmMlbVhuED7PYERd/J7GiOY6g/VOuaPxax4SWHznaHbjVRfl5iWAlQOzIJgvs7NWa2LvgdCbgHIDImyS1GUWuQH3ukHp6YY/Kt/o6Vq9xYSPDaSIghpyAPJ/oGEDSyxSSEQ+Q7DJRrsMlQamK75XjmOsUo0D6G0wstsEOJ8Vx7bhCOX/lwCIGIP4ujkf1rTKr0nrwYQEUjageW7pbMDJKlB6ajH+ALGY3fAGSxOdMa+mw9WQlZwdoiWSdEeey8+7TuuZys+bKLsTV69jwAPepd00+D09QRBAmRhAQW8nVoOF5Uo1WxUKpQko6VHkaA4yWKkoaEMlFJ9KRZ/TGmyJeEvcIN0+voZj8AgVHNmka/QjmMtRVULWgUwAXdSIi3Lcd0TNgG9GJLHiF6H8DlzKGgaTe4znJQByt6RbpDZCZwLODWg2nSmp1tHu+bULyn8QTfeuWqMlmCk9xRX0ZklrmuX2NKbGaL0FH79RiwE0aZUL7yYOF3GAUotBz2TGQUqXSWghqRLAP4jxzO3qUSQUJuDqAcLNUpAxT2reog8RAU0K+t4J5f+AEYfsn4fGTJd0EWYP1jFYGyL2qhEArb+iNVjk9woCcBDAHxnx0LvDVOYiqbzHZ5HYE0QGIJCtACQAQp2ORRSIo+Whb8uR+6sditOyyxClNRSiIprZwFGPEhdzMWy1eFwXWoD5+KAsQQCutQKflFfKC0UJaEsA3QAdQhNB0XhWIZiFWCfn6akZ5Ac5XUi5+mGo9HU17ObPwf9r9vzzZQRQUBOfywrVgiCWChwV8ARglwFykO/qiGUxkdv4OgF/w0tBLwigWrgDFknb3OoI3plY6i0E0QQV/VY8ALewctBwi1bjKCOWrrklm6XtvCHB+nx0XczkBixSIwAJ/dxZfcYEXAzAPvJfhSalP4t+/Yn0BPghNZE1+lCp7+txafBybBpsQmxGbB2WBnvx888OyeAtA/4S3+sbBQFUJ5cgzCoFNbP+m38vnYNHha8XniOF6M3efZIxW5XnVMBTC2DpNTZgzHdS+Mv4SKnN95NTYO3gTJiNBJfadSJ0bTcNWrbOYV1+TVDBr4kwQwOTGerLoNJfUnzaCqzji/Ps18plwDpRCCTEZ4QqGR0EkMtDAFN6jId//Pymv5gVB9/h7f7i0HTI7TWO1TfciIpe22hhwTz6O+kxSHZ7NCrgDPS+gxbALZqWJTUjUhCSP7qJ4gwK8bLL4jiQU9X6AkgxJnSfwBTI7257+aanxh0isYjobKhrcig8wUlldrW4az9iPqI7WgINgo15JdZhcPNckR4U4vsEMBGV55KfEADItz7d9lSv36v9VGa6K7e7xnsdlpQR2ImYgmgWbLLVVKwCXeuZ+I4kiUMpxOMEkM1DAJMZAfiBqS8r/n13joLottNZClO56X2o1ZrKrz939JDYojRGWxDLIukttHxWHEwhHpDbRjsVA5hKMYAs367Npwg+1St0iJkGwQarLyp+efiezZTQW02hYRZHo1dLi8frQoRUN7l+CPqgzBed5c9ZAJDr8t+JHwFDOk0uCej54QAWKiO/S0vl2RE2R8dm6znezxYJCUzRhZsljYk1BS3mIYC5fcf4XCEQ3frH0hJgft/R0DRyhr/c+BWBXLFDiBEao7W2xmCTgvQIg2gjFlLl/j9VLlKrsfVhnqEg9/lQJaBSsUdDOQd3nAwheOsHVeEwVI2cBgySMwVlEaS/Mk3oBiI4w4aIGKwRtUyUMsT3KiIX3TaRLRBSZQRAfqYlRC5XrvBAhhit8OhA3+gFIMWndOT6IRlgaONYza2ppMIHsXiBowagDpLJda1y2cIPCiL2bD8VBnWcAkPRvSCy6dNhKrSLmQ7NW+fADfh91CilWElusEA+1dAwGIMthHZRSBGFUpBJxAaEVF0GoL48T7BCBaG8+fqhGV4nAPL3T2fGw71ojVCLcpC+skrv+Nuo8i++82Tm5tCcv/2Jw1mt/2/oXvyRHg9/ZsTDXxmOx5OIY+kJbCvQe0kpsCk2HZbg8xnbfQJ0jJnGxoTTmDAilCqySmh+43JEU8oSBCFxa/SiiEhI1RAANS19qKYsVPZKQTZv9gKQ8pPyWXuNZUob5KLik9KH4i1vROuBUpsbhqbDV6jsRCxKmTDrDyjlapQHKN1HgLiAVgkRw0Ekj+UDRkJyl0nMiqjCbMR2jcHSNiQiT9KUGusmREhlCKCZPCW4wk7AppG58ElKstcmAinVfKSwlNfXuKj4VNM/AM15ShV+jUpP2QOlEcheVZ2EcscgDQz5GF+zB5AM+nWYwnoKqoAI/ouIR9ctSBkTJ0RIZQigO+KUGgHo2+TAT2mJXiEA+p1/oPJPQuWnWISzCkRKVw8tBkoR0lATGuSh3PCe6TR0DA+hUuSMrhOZi1DJakRaNT5NxyZI0ap6iyglFuKc0MwCmQAyVAaXMAXq0X4q84XtXgj4/Y2mOTXuOHvz0/dSt177mOnwzOBM5j6QMtq92IxE7cbvJIxgU5avrZxFQANl5qIVUIe6S1mXYdMZ4mAL4ZOgCCsrOeUtAsrCm8vTY8Hpd5FfvbDfaN7lG1dsNKJIfl7vsSXDTO0+1JVIRLAFLYL+6I6Eup7CvIBYqtFbG1BTUUirfElqPk0cbiEc5j8NMTXZtHiAnuQxoed6aRjIGry56aYMcjK6T+m7zWjuU7oQfLg9+Ti6Ng/0H8myEC66BTRwdIUu3NaAuQP6AkmKHi8OuBAu//8axD7VDcF4Qz2FiujJFCApB03doVw7b6qPnitF3OM7T2LBN1+59dXiG8VyQVMiPm8XrQEigeX4OtVnxV0GsXtACB8BhKllAEpSgAmeSwGSUtBIrj58E3dLnif1AFC/Pw3r9LfRZY5GpnhYhO7Oja7VN1xCLGPr36i/w1ggDrmQq/j/eDhkAhgsB5MqzADQLfy1h5aCKH6/rddY3nFbTPkpRpCP/j4V6oAfjyqjbstXYtOgddtsVywBCuYuxNctxPH+iv4BIeVITeNMNBPZeKo8Hv+fAlWnMjyTASAleBUVoAnfsM2Sm39mnzEsW+Dvm4uUAiOaU0ivu9b5uAD1EORoTHlBjqnPok5ASHkBQGMe3RLP82QAKAV32UPK/zOa71R7z2P6a+Qeheye41iZbiCtLSOXgIaaUN1AsPMkcAKRJsXMZ/0eomxYyP/6/3orjan+VE3BKPf+hAcXglCNf4iR3/Qf3mUSi6QH4s5CJUtA1Y+hzlc/fo/vce9gtmbO4rFtU0J83v9XtgxbeqhVANKBo1z6fg/sBKSf/2lKMhja8EX96Xuo8eb/hicF9L5CIjZyv8gKc4EEDuP7rNfQZKFmi8ThF4L+P/r+OodvmKs2B5CULCo6G37xQAkwjRunIB7PAafgGM3s3xaXWi22FSskMK3HOFf6IF7UGC2NHHUfIjMgzH8yCU028v9f4PH/R3Wb4PYKQLrBaQtPC7kYhmc2wby+o1nE3F4NCODffoh4V/ohaPjoQo3BoqM9BGIXQXWWpjOU9N/tiK/UDg/1tD8ywP3+PwUY5/Qdw93Y07v9VLRKEqrF7V9eRyT1ETiZHvwTkRJszGdr58WMwWoqod3ylBVlifKyigr9f+paO5jkXv+fDvW3IxKZq6Hm+9NzahRhZnv6AtnvV7OWaBDJoI6Tna0T+BjfeyPNEZAM+UIZqmUAkJi/+SQaO72U56bt3G4ai0K72/x/fFAml29LB57SYtRnbx9ZPQmgxGVKTmFdjk5WDK7ThpvrUfegqA+ohkLsj2iMb/5BdQKwwfSe49y6C1Bp9aXaffp9PBbJ216eSuRLJECvBW/cpFT3YE7NCJtj94AhVyhFtQn+RcxxFAAZrH1kn1C1tHbdEPfOAKRDfCQphU0bCuKwSNLw9j9bzW//sgRKTVq08syJoOB3iPZUJRgSNlgoRvW5/S1S8gA7EcAinjRbGN4sX7m5/p8IYGn/kao1/3S4aZTXK9XY978aAZxDQrT1HsuqBZ1wBTZpjLb6ynJSIdXBAtCzEeDX4pt+gCf9l4m37Tk3pv/s8nRfmsSrZv7T7d+tvfvjEf6aGaCMyGDngoLkCkyRWtocDUPNRX1AgJv/s5X0Xy8e858Cco+7ufyXDi5V8TWLmsF1cBf0Gy2UvwJLiuYJ0NxGJ0jgC63BEqkzWqR6bbKFkgS6+S+1HE8EcDeP+U+jrD918wRgIpeNQ9PZsE4NRznyPg+UI/u7O/DYwCzV17MMVmvCbSG0hFQbLmoDAlJCIvKV2/8GxFGe6D9Npjnt5mAbkQst4VDr+lMGkp4Q5j9XRoWKhIKcKxAaygaItBSzBANS6rcrYmum0ddTLf5Rymwd1X/uPayUy09GoqnB4f/TVuLLQsm5XAEahRbJUVRVCm/j+WjC5gkaRZlwwAk1/gQbbDp8g5/mMf/vQPPf3QtA6GfT2K7WbSsuZFGGfawdnOFzW4l9OSj49KBMtq9Qwz9PMEe6dR4SALkBRUJpAsf3Nyvmvx7xrZYz137OA+Y/3VRq+X86wLR8k/bvCf+f37qi4SipXSY64wp8xuZDGtEKiBRWQMBIkDFXCtbnEQFMl7vCVG/bZzxw25IyvxGXylZlaVQsklasHbn6Nf5U9vWl/YR3cGZYZCyWV8VLUpiYJej3UsuYpwz+aIiP7/AM2CBl+zbV/b3/RDBENLVV6v/JIqG13H9mxIsAoAsdlpQ6DTY6MUHIaG3jWDAirAC/l+ZR9yobZFUn/yoEQFNn/vHIDRUL9/cfpeqjUoBwdLcJbEqwIADn3Sza5di9Pf9odVowUtNo1WqQBGq1ElaAnwf/rFKwwULBv6d4ZuvR7P/t8ake8bXpcBb0HquaAaCvU5mrUH7XXQHq56hv4u4VOIboxkaISaOFEvmrKO2eiCi1xR8lo787TGHLM+0eCFLRuq5x3SeoEgD5rzQkVGQAXH+tyX1ydFtyWwFP48URTBeIJFwB/yUATacFkmN7LM+ILQusGJjlscUfVANA03wrIgBlJdmTgzIFAVTSCngrLpVVU2r4V493o8Wx190gBof4X+ovXFn7bbmRp/KPbllDm2z40oObf/7KjIfYTpMrvJXosFIu+6XYdEEAle0YRItrQnenKgRXa8LJfUQLICpHKJVfpf5aWJWxX2ly15cqAZg9FPxTDiS5Gv3Q5VAjAEoTUrpQ1ABUQVowaTjcEsmdFqRYQGfqFKx9xxyhVH5l/tPUH6M1FB838gT/qNDm3UTPTdkhAqC6/q7tpqkSQGMkgF0JYgJQVcVdpvUcx28FGK2P1oxwZAREdaDfmP82JfgXjfiNJ/iX0sX9jT9lD+MxJIB2MeplwE08TE7VoWX4Nv7ioJ/RAohm1YFRYmiIf5j/LfOkkAhW/mtVW/pBCkatoy8MTfeogikE0JajD4ACVwdEG3CV4WLWMMhBK8CJduHFtfWFNXRiy7C/mP9swks9fOPe5Ln9abWWp8tsnSWA/YIAqnwG4638VsDnWqOtOZ0rQQI+n/pTSn+trXnMf8L8vp6fskO/j0Z70UjrmqougFm4AG6IBdB2IU4CKEaYa+jNUrBREIBv+/8t8yWtY/HnJJ7Gnxu8ZF7b5e02PEFAqk4UY8Cr3grYnTCCjVjndAUOafXW62mmhCZ8hlA0nyUANvOf9f0/w2P+D+g4hS2c9IYFQGnAPh2mqhIAjbt+bZgHJgFnycgsA+XzAWYF0Gh1avvmrA6kVHI6TQ0KajFZKJovp/+0Bsv1+PgRT/pvUb/RXmmxVfrVh3IUAlGQcsNQNxUCKco9HpGLuAtxH+IBxFLE3YhCxBTE6MAiAiLUrUisjfj3CWzW6C21EZIUPV4om89JeIHi/3dC/MHT+LPTS6a1cgOl4g2k1gvglunEiiJny8q+CbELsR9xGHFExkHEu4g3EU8h5iDGBgYR2OV149RqzWkF/K4zWLuwBrOWhULffE6az1cIYKKa/0+R99bR2fCzF4dsXEIlokBUDY51YEuqshlIufHphn9LVvT3ZBwpB++VApHB87JVEAAWAZH/6kGZrN+C0wq4X6fPqakV68V90/+XDGba9/YAj/8/rJ0ZTqYOx5sg1muHb2afMVztwPm9x1YNUZHCTkKskW/3qyn9ERUy2I14QnYbRvovEdBrSluG27SdzmsFfCavlZd0EaIwyPf8f72lDj6+xuP/T2g7B74YnA3/ZMV7iQC8MBBkHOJpJ5X+akRAj9sRD8oxAj+2Bor6juEtCrqELsBYbTi6AVEiJeiDBMDm/n+mpvx1jTZY0K4I9nSbD78kjPEaAawdnMk1EmxgVYwEy5KDegdcuPkrIgKKGbyKWCgTTJb/uQHvJztVGPSKxmCpLdwAn8wAWCMRx9UIoIkpD1Z3nAc7uyyCA71mwd+pIzzuCtDBo+lDjTiGgkZFZ7MR4lAZ5adb+rUqVP6yREABxPWImf4VHyBSPY/WVVY37pTgcXy/OrKK01ZzheL5GAEMQPytuvU3Ih82dlqABLAQdiA+6m+Gi5kJHvc/ecaC09foe1zeU5AlR+4fLxPhP+ImItiDWO1f8QEi4xc5VrSVwgIpcroj7iTEF1KAExUCGCMveahQoTpHFsKWzv8SwNtdF8C3sRO9stGWbbAxqBcDvU7FQK5G/FfKpv8RD8AP4wOO9yIROsRwBwOPIK5j48ONojLQ+3JHsqQzsD6AQtUMAGJI65nwpqz8CvZ0L4Lfk7M85gooxUBDVIqBCDrEQ7EjAcbGqlfmKV8nMzxfTtsdcpPpzxMf2IJY5B/xASeCgWfYPkEkgLBmi4X+eT0FaMyVQlqy9d/38RBAZvRseLsMAWzvsggO9y6E02meSw3SBCIaUKGaCgy3Qfb4cXCZ0nfzEFNlhRpVSuFHyZ+bKlf0rZGLezyt+OURAVkfL/h2fICsgEOJw+GmSO7+gBUaw4wgjQgG+oD/r2cZAC2+KU/wMPiUtnPgnTIEoODjAbkeiwdQJuDB/iPZDV8haYVb4c6kKXBqbzzYD8jm9Ytydd5jiFVyem+j/LUDKsU93iICig88iTD7WHwAn4d9zDA4PSce4hMms9ebq03YYL3NsVBUrBX3BQKohW/Gi2pvXC2ELWbuVQlgZ9cF8PXQyXA5K84jwSfy7RuqZQLQRWjWbQZ8tTUJ4Ggp5T5aBr6m9FcrJNqBeEi2VrzZbKT83lwHMcH+YbDq3iyoZbLwEMBFRAYRQLApRyihN4XqsxGqRUCkZHWMNpjbruiqBEDY1e0uj9QHkNn5f8OT4HaVHLQGCaBhGzNsfSLNQQBH/BxKfOB1xP2lAoVZHlR8cplyEMtlqwmfF722n72aDC265/CuFl+jM1p1OqPIBvhACtBSHx+38xQBLWxf9D8xgCvjAQthX885cHJ4ulvjAbxtwQoJLJozOjAIoDQRHJLrEx6Ub+LRpdqQq7rrMUuOk+TLrtN2mYhkq8mOuHAgDkaPn8DrBnyNaM7OnyABLwYB2RwAKy0A3aNGAPWRAO5pf1eFBKAEBY/0LYAzaSlunRdACyyzOQOBiZmT4My+OLC/F0AkUDp1+DZiLWIxYkapzEFmGSXmUXTl/9FNPxGRh1iGeAmxt8zvLQU4GgvrH86AupFcNQHkBmSxKdQmURrsxSwAGwNOBPCuGgE0QAJYwkEAO0qKhCxwISPRbSRAgcDVg7JY269aHCC8Zw58sy0JINAIoGyMgKyCd+Sg5iqZEOjWni43M42XyWFsKdC/JyAmy+QxR+54fEq2MPaWuu0reP3otf3ujUSI6JPN6was1bE1YiIb4D0CoDVgerYCfC+PBXCfEwRAxUKfDcqGS27KDFAg8GhyCtyokn4iF6B+lAU2PZrObqmAJICrtSEfkhWYSGEbYjNig1zjsE5OMW6UexK2y92K++Sf40Jw9NKhOJg8ZbwzbkAzsgJqmXKFMvoDAdzjBAE4KgXnwzexk9ySGeCdD6ikA23msYGv/GqEUDYLUt7XKvG7iGA3PJLO6wZc0OqtabRNuFHUJKGM3gsCWikIuLMqgoDlZwbmwY/x45jP7o6CIJpVX1MlDkAE0C12Kvz+TkLgxQF8CC64AY8Fm6wakQ3wLgFwpQFrIwHMUUkDXi0zsLv7XfBr4mi3xAHWD8mAuirNKOQGNInJhd3PjgisbIAP4iK6HZP43YBP8b25mfUGNJ8mFNKfC4HUSODdHnPgeHJWldcDfDE8CVq0zlHtSScSmD9rtLAA3G0FOJcNOKvVW4axOEDr2UIhvWQBUCnwU5UtBd7BkR7c13M2nEjJrLLMAP2cM5lxbEchjxvQO2Eq/LE7XpCAm92Ar15PYpkXTjdgidTaVkMj3AAvVALqzZI0BogElrraDOSsJUCDRKqyUIjcgBUDsyDEqG4BkBuwa61wA9wJKgo6dyAOMsdOZDUYHASwX2uwNdKKGQFeIADjFHknoHU2DwHEtZ4Fb1WCABRL4GDvmXCqikiA0oEfJqfALRyjqehGKrSNEYrqATfgsfu4ewP+kEfSS2JcmIclWJ+tuAFT5F1uFRJAj6hC2FpqIEhlSOAQI4G0SpMAuQF/Z8ZDXOfJXG5A+4HT4ZcdCYFbFOQTBDAMPtqcDLd2nsHrBlh0RpukCRfdgd6KAySwgIzKRCBTq3zYVAUEoLgDh3oXyiRQeSuA1w2oF2WBF1ekCzfAnW4Akutfe+NhyAhqEeZyAzbrDJZQYQF4jwC4tgLdZMqDdZ3mVwkBKCRA7sDJlPRKkQBlAz5NSYZmrdXdALICMsZMhHP745i/KhTWfcHARbNHM9LlIIDvUPlZc5B0W5FQSo8TgN56Bz7+qEYADY02eLDDXZUKBJbnDlBg8I+UjEq5Aeey4iCTY2klmaS3dJoB729MEVaAm92AnWtS4dpoMw8JnEck0Vms007sD/SGBUBR2MM8tQD5LtYCqFkC+3vOhuNJWZVyA14Yql4UpOCuQhEMdLcFQLGWtgOmQ1A4Zzrwtjk1NHrRHehhArBIWqOFioFeUHuTyLzOqmQqsCJLYG+Puaxi8LKLbsDPaYnQjmNCLbkBbe6cDt+/mSiCgW7EpUPDYPLU8bzpQGpJbyjSgZ5OBbaySEHNWCrwbp5UYK+oQni9igKBVysb/jFunMsNRHP6jFG1AOjroREWlqoSboB704FrlmVC7VZcVtkxrdHahgggJDxfKKanpPaNk5zaDdA8Ih82dHIPASgkQA1ENF+QWontTroBh5OGw80qS0MUK6BPwlT4fZdoEHKnG/Dx5mQWc+FIB9Jm6vFkkdZpIcqCPSc9ipzKBFxjtMHyKg4Elt9KvIDNEzjPhorE8gcDM/mCgUpK8IWHRUrQnenAU3vioV/iFN7moFU6g02jE26AFwKBRsuN+PhftTcpGJETM6fKA4FXGyryYX+LvHOA3wp4JVZ9YrBiBQwdMRn+3CP6A9yJQttYXgI4ghZAYxEH8DgB2CRk3lB84TfxxAEGl7MhyJ043KeAO01IRHEiPR76dpjCZQVc08YMrzyWJqwAN8YBXlqZzqwtjnTgCUQHtjNAny0U01MSYrRINfRsRdgcnkxAeJkloe6Go5NwDhs5zhMcJCtg9SD1FeKKFRCXjlbAXmEFuCsO8OXWJGjeLYc3DjBZa8yTdGHjhGJ6SoKNViUOMFje36Y6IHRpe/fHAcoLDn41dArbQFRRXEBJCXaMmcZlBdDugM2PiliAu+IAf78bD7Gp3JuDntAazBpRFuyFOIDOsbLpKy1HGm1M9GyPWQBlNxB93N8Mp1MrjgvQ15b1HwnBRvVDp8QCTopZAW6zAuYWjOFtDKINwteKOIB3KgKpIOglHjegQ2QhvNp5gVdIYAdrJJoJx5NGwuWRcVe1Ar4ZkQRt2k7nzgg891CGsALcFAfYvCqdTWfmiAMcx4somhFAVI5QTE+JxmSRdHpWEJSLsKtZAI1NNljZYZ5H3YCycYE93e+Cb2MnXdUlICtgSf9R3FZAj2FTRauw9+MAlxCjaFydNL2vUEyPWQBGi2IFdJCjsRW+UbSZd2LbOV4jgNIuwUfoEvw1IrVyVgD1OkRYYPmikcINcFN78ODh3HGAByXjjBpihbinSUBP6RfLNWp7AhQ3oH1kgVfdgCuaiXrNhp8TxsA/WfFXxAbo46VoBYRwWAHUtBLVLxv+77UkYQW4gQRm2sbwEsAurcHSQMQBPE0A4WapRqeFZAXM4wkENnJDe3BlXIJ3us1j1YNn0oZfYQX8kMqXEVBgs4xlW27EvIAqnha8nHta8E9IAGGCADwsePsrbkB3xEkeEkiLnu115S8LGjJCXYUOayCWkcDjg7K46gLIR23aUewQcEtfwMvJcHOnXJ44AE2nYuPCa4YLN8Ab6UDVjcGKGxAWkQ8vVOGUoKqyBqhm4L9oDZxOHcEmBx9PT4C+HOvElYBgcuYkUSJcxS7AiV0J0D12Kq8bMCvEZJNqhIk5gZ61AqgqMCyPa1IwIRR964KYuT7hBpQHmjbEVpOhNfASZ4+AkhZcfX+mIIAqxD+HhsHUadzzAdZr9dYQlg0Q4kECMJRUBbZF/MpjBXSJLIQtPhAMvJo1QEtKKVPwU1ImpHWdpNoqrFgBFBD8fEuycAWqyg14PxZW3pMFISYuC+AjVP7rRRzAS26AxlEUtJEnDkCzApe0v8tnrYCSfoIec+HZXma4MYJvbBh9z/Tp4+D8AREQrKo5gbueHQGN25p5G4PaMwKIFnMCPSpBzaZI1JCBL34m4iKPFUAdgm/4MAEooMUmadGzuLIBdEjpsG5eJboFqyoQ+MObiWDolc1bEJRFBBB6+wKhlB6tCgzLVayApvj4Ac9N2cSUBw97sTKQe9AI4tlO80HfKp/bFeg8ZBp8s03UBlRVY1BcGve+gMW68AJWpCbE40VBZikoejl3MJBIIL7NLI/OCajMoBGablwHXRceV4Bgzh0HFw663xWwH4kFYBiKhFMK+Dk7Q7UqCHpFq7fWFnEALxGAHAyMcCxuUCeAG9AKWOEHVgARAAUtacBpEKcr0CTGDC+vck/LMCk1KTh9fOrgcPhy31jYuysXtu4sgC07C2HHOzb4cO9k+O1AOlw4nMAIwS5/vz8WBK19MIN3UOhnSAA3CgLwliugt0o1W1o1+Aas4LUChvlJLIBI6hEkK9p2xEMCVCbccfA01tRSla4AKT4p9dE9U2Hp6w9A2sZN0GXdLoh+dh9Erj0IrRCtn90P7Z/bC4Ne2Ab5r6yG15EY/jg4QrYK/C8QeHhDClzfPpcnEFiyOFSSkoRCelrqtM9F/6tkYOhvPARAXYK+Uh7MA2poCuF0A+jvmzRlPJzZF1cl9QF0i9NtP2fLY9Bp3W5o+cxRaI5oWYL3SuEotKCvr3kfieEAZL60kRHB6UPJJdaDPy0MoRQrd2cgnsFaPeYLhfS43JHnCAYarTp8XM2jJHSb9ouaWSVbhD3hCtCy046R/K5Ag9ZmeLIKCoTo5iYzf9iG15hik4KHoaLzgAiBiIIsg+kvr4XDu6fDpcPxfkEE9LoRgVKlJWdB0N1BEbMknT5X6KM35KZmmZKObQ9i/QG/89yS9Yw2KGpX5BdWAD3HpWixXIeugIbTFdD3yoEjL7q+W5AU9cjuadBv/VvsRudV/PKIgMijM1oPC197BL54dxwjFl+PD5AVMDufOxC4MdhoCdUZRRzAO2IqdLgBJkswvhlP8loBbVoVwIudfN8KUNqJx0bP5nYFyHQdmjoZftvp/PAQUk7y30e/tKFSyn8lETjchf7r34TVb9wNxw6kl2QNfLUi8JkHuDcGfagzWJuIXQFelEZ32JQS4Y6IX3iUhJRpAvrXO/wkLUiuQGdeV4D2I5isUGgb43RqkBRz3VvzwLT2EFPasCoEWQOGtYchdeMm2LJzps/GB8hy2vf8cGgSwxUIPIaIEpkAb0ori6TRI8JoWqv1AV4roCmlBTvO8xtXgDYe8WYF6OBe29YMzy/P4LYCKH330d5JMOCFN5iyhlUxAZQmgqhnD7D4wKHd0+Gij8UHlIrA8J5cI8LOKavDNfoCoYvekmBTPlsggmjFMzlYIYE+UTN9tlGoPExDqyVUvuV54gGmPtmq8QCluOeTvRPZ7dzSjcpfNj5A2YUFr62AL94dW2KB+EIgkFqtByRzrwzL1xnNUlDLmUIRvSbNp7G6AOnmAnIF8uUlDqqmcm2jDXJj/McVILLq33omd4Ug3WB0kH9868pV40pxD936f6MpvnnHbJbH94TyXy0+8MQbi+FXH4kPlLQGh3FlAh7XGfI1OryAhHizOtDRH0BpwRt45gYqVsAtaFav7OA/rsDTHeez7UdBnCRAA1LpMFN6ixSeDviZQ0nw3f5RsAkVf9Kmdcwkb+Fh5S8vPpDy4svw6s6ZjJS8aQ1QIHDZgpFcry9ip05vrS8CgT4gQZFWSRfOAoLkl/3NSwLdowrhZT9xBYgE5rUrYpuQNZzxgPpRZphRZIFV2+6FRa89AhM3r4M+z29nwT6K9rf0kuJfLT4wbfOzcGB3ttfiA+QyvfpYGqur4AgEfo24WQQCfUA0JtkK0LN5Aas5GRxqyduE3vSTWAA9z5FOpAbpEOvQ1blp9hZo/swHiPflAh/fUPzy4gMd1+2GeVtWwmfvjvd4fIDcpU9eTmbzF4OcKgkW4nUJNeU4ioMMVhPPSvHSU4Tn+0mBEFkqm+WGId54gFZvgdrdFsBt926HsLVHfU7xy48PHIW+67fD8m33w7f7RpUQgd0DBHD87XhoN3AaTyDwAiKdCCAoXJCA9yW8QAoOt0lSJCOBcYjzvK4A+dar/Sg1SM81zIl4AJFAvYFLoNnDe/yCBBS3IBwfB77wBix9/UH4cO8kOHc4sVQbshvand+LhZ/3psGAjFzeTMBsnYma00Qg0DfSgmyJiFXCA18X35zntE401HTDW3VjJ/+JByxAq+VaJ2YHEK5JeQRaPH7Ab0hAIQKyCKgbMeflZ2DD9iL4at+YkoKiK+cSXJ0Y7CX4V9np//5zJA5OHExlvQsPo8WR+tJmuHnsY6AJt/C8puhuWrTCDfAlaZHN4gH4phgRH2udiJontpnlFw1DyhixSVQfYLRyk4DOlAeNxzwJLZ88hCTwnt+QgOIaUODSuPYw9Hj+bRi3aT08+PpS2LqzED7ZO4HNJfjz4HBmJVAQ8XLp9B4q+fnDCYw0SNm/3z8S9u2aAc++NR+KtjwKSS++Au2ee9cRh1j7Adww4wXQGrlSgTsR9QUB+JDUMuaxpaIh4VQkZB2B+IvXCqBpPFNQqd6S/W1/qA+IbT2T2wLQUlAwsgCun/48hK054lcEUNYqIDKgR5pN0PG5PaymIGPjS5CNVkLhq0/A/NdWwt1bH2bZj7lbVoHlladg/KbnIX7DFui+7m0220D/zJGSn1NSC/HsUbilaAsEo0XI8Zp+ibhJEICvZQWMFrlZyEbNQvcjinlJgNJshTFz/SIrQK7A+k7zoT1nv4ASDwiJngU35W/yWwIomz1Q5hIoxEBoVgbK55Xvu2rxE7pHty99G0JiZrPXSuX1/F0eVS+UztdEF25hi0XxzaE57tt4b0lSpBvRVL67fZHfxAMe7TgPmjkZFKzVsQhumbfVr+IBHgG+Hs0f3Qe1eyzkIQDqCUhkBNBc9AT4lvQokiSjGS0Bm7JQ5HNnSOD2iDxY2v4uv0kPLkTCuo6zaagkPdh9Ady2+E1BAmVdjNUHof7QZaDlCwTmkrUpNZ0tdM7nXAHqFjTYJF1EDrkEKTzLRUuTQAu8VZf7ySgxmh9A/Q31nMkMIAnU7bsYTd6dggRKY80RaJTBnQlYJjVfKAWJngDfFNYtaCQSyNPIDUMXnCEBqhHwl6nC2xAZcqWgMyRQb9D90Gz5bkECMsKfPQrXT32WN7i6UWe0hWoFAfgwCVBA0DFItI48TdjuDAnQwg6yBPwhM/BK5wUw0JnMgIwGcQ9C8xV7BQnImYCmhZtBh+87x2t3CNFIBAJ9vUgoLFcpFb6eLXdwQjkUd2CZH8QElMwATRLSOEkCDZMeYQGwak8C+Pffds9bLFuiVe8J+EFjMN+uNYhNQb4t0UWS1NcqDxCxtkTsdpYEKDBI2YEdPl4nQCTwVMf5ENmqgD8oSDDa4JoRK6HFY/urNwng397skT0sU8KRCTiJ39NZWAB+4QqYJZ0pV9LoGQm0QbzvLAlQirCw3VyfLxZyLBm5C5o7kx4kmGwsAOZvJcNVSwDvMRKs2/ceHgKgnpMURgBROULJfL4+wGhBV8CsbBru5kx6UCGBa+SKQV8vGyYSuAfdlhudSQ/KJcPXjnwCWjxxsNqSAJVLN4h/iD8VSJOpOkwSCuYfmQHFFZhBH/eVSzrBmeYhKhum3oGNSAK+HheY066IbUoOcqZkGN2dxqNXV2sSuDbrcd5U4JLQZrNZBaoQP0oPagx5Ui0jWzjaX57w4hQJUANR16hCeNLHW4mpRsAWMxcaOlUjIJPAqNXQshqSAKUCr5vCnQp8Hs9TiIgD+FuhEJEAmm6hJmohtg5ylgQUIqA04aL2RT4bF9gpTxOa2tbZQiHFEngSWq6uXiRABED9EpypQAooNxQE4I8koLcyIgjVZ5Ml0I+tf3aSBMi0boyKNT56NsvDv+3DhUKj8TnWdoUExlQzEsC/89aF2yC4zUyeVOCXWr1FrAz3Z0uASjlDwll2gPYNfuiKJUAzBnujS/AYugQ7fdAaoOdDgcu06FncewZKSABvwmoVE8C/8Y4Hd0Gt9nN4MgG0KShCEIBfkwANFTVL2giWHYhBvOsKCRBuwxuThnVQQc5OORq/08fmCKS0mcUIy1lLgAJj1SJF6FxX4EmtwdZVEIC/Bwb1cgsxEoHGYGkpVwzaXXEJguXYwDg0uVd1mFeyiegdmRC8BeU50PNJlEnAqYEipjxolL7KUSyEfjIjggAExQCaPbKXDVTlIIBTsuUolMj/i4Vsct8AWz5Ky0aeQFx0lgQUIqBMwXUmG3SMLIBMJAMqIqLV34+jm7Cm43xY28k7eBZBi1E6RhY6/XdRsRBVDFIX4R0P7QpI3H7/DrR2nmBWD8drchzPjFgWGjgpwlxJ6txPorVPGqOtHr6xM+U58OAKNDIZEGiGXwOjDRqjElH/vjdxPaIh3+y7csuGaWpOSLs5gYm2sxjRcb4en2odm6mE8gSMROVIIWFsrqCk01uolXi4swVDarECX4HLfwuZxoEM/tfiWSTEYDYYREigWQOsjViq05wFB2kTzA5X4gICAQtyDzO1hjwpKHyKUJiAzBAgs2scxUIUF6B87zLeHYQCAY8DGkeLuaQh11FIYIoOSUAXaZa3EVuCHazvfNGQQEDhNCJVS81lYiJQNZDo8ZIunFwBiyQ1syl7CJ8W1kC1BI2aX4bWYYiSNRJSTSTYaGHQscWQ5lA8CLGItxBnhWJUC1xGPKXRW67V0mwJfZ5Qimon+hypvmEumzxMASCdoxkkAbFZXhghFCUwQZOlF2v11kZ0AdQyFDDLUEh1jQ2g/6fTT3ekCx2ojR93QMyRMwY/824qFvBpULXfa4hBmnCrjtzAWpFWSWppFkogxNFQVNNhCTgChVFsSWlDeSnJBMRyxBvywtLjsrtQLBTLp818Kv56D7ESMRTRQKN3ZIO0ETT8o8hj5+v/AceICmF+bnRdAAAAAElFTkSuQmCC"

