"""Automatic locale selection with complete EN/IT/FR/DE/ES catalogs."""
import os

LANGUAGES = ("en", "it", "fr", "de", "es")


def detect_language(environment=None):
    env = os.environ if environment is None else environment
    locale = env.get("LC_ALL") or env.get("LC_MESSAGES") or env.get("LANG") or ""
    if locale.upper() in {"C", "POSIX", "C.UTF-8", "C.UTF8"}:
        return "en"
    preferences = env.get("LANGUAGE", "").split(":") + [locale]
    for preference in preferences:
        language = preference.replace("-", "_").split("_")[0].split(".")[0].lower()
        if language in LANGUAGES:
            return language
    return "en"


LANGUAGE = detect_language()


def tr(message, language=None):
    return MESSAGES.get(message, {}).get(language or LANGUAGE, message)


MESSAGES = {'Invalid image path: {0}': {'it': 'Percorso immagine non valido: {0}',
                             'en': 'Invalid image path: {0}',
                             'fr': 'Chemin d’image invalide : {0}',
                             'de': 'Ungültiger Abbildpfad: {0}',
                             'es': 'Ruta de imagen no válida: {0}'},
 'Name incompatible with FAT32: {0}': {'it': 'Nome incompatibile con FAT32: {0}',
                                       'en': 'Name incompatible with FAT32: {0}',
                                       'fr': 'Nom incompatible avec FAT32 : {0}',
                                       'de': 'Mit FAT32 inkompatibler Name: {0}',
                                       'es': 'Nombre incompatible con FAT32: {0}'},
 'Conflicting names on FAT32: {0}': {'it': 'Nomi in conflitto su FAT32: {0}',
                                     'en': 'Conflicting names on FAT32: {0}',
                                     'fr': 'Noms en conflit sur FAT32 : {0}',
                                     'de': 'Namenskonflikt auf FAT32: {0}',
                                     'es': 'Nombres en conflicto en FAT32: {0}'},
 'Duplicate names: {0}': {'it': 'Nomi duplicati: {0}',
                          'en': 'Duplicate names: {0}',
                          'fr': 'Noms en double : {0}',
                          'de': 'Doppelte Namen: {0}',
                          'es': 'Nombres duplicados: {0}'},
 'The Windows ISO must contain x64 UEFI boot files and sources/boot.wim.': {'it': 'La ISO Windows deve '
                                                                                  'contenere boot UEFI x64 e '
                                                                                  'sources/boot.wim.',
                                                                            'en': 'The Windows ISO must '
                                                                                  'contain x64 UEFI boot '
                                                                                  'files and '
                                                                                  'sources/boot.wim.',
                                                                            'fr': 'L’ISO Windows doit '
                                                                                  'contenir le démarrage '
                                                                                  'UEFI x64 et '
                                                                                  'sources/boot.wim.',
                                                                            'de': 'Die Windows-ISO muss '
                                                                                  'UEFI-x64-Startdateien und '
                                                                                  'sources/boot.wim '
                                                                                  'enthalten.',
                                                                            'es': 'La ISO de Windows debe '
                                                                                  'contener el arranque UEFI '
                                                                                  'x64 y sources/boot.wim.'},
 'Exactly one sources/install.wim or install.esd is required.': {'it': 'Occorre un solo sources/install.wim '
                                                                       'oppure install.esd.',
                                                                 'en': 'Exactly one sources/install.wim or '
                                                                       'install.esd is required.',
                                                                 'fr': 'Un seul fichier sources/install.wim '
                                                                       'ou install.esd est requis.',
                                                                 'de': 'Genau eine sources/install.wim oder '
                                                                       'install.esd ist erforderlich.',
                                                                 'es': 'Se requiere un único '
                                                                       'sources/install.wim o install.esd.'},
 'Empty Windows file: {0}': {'it': 'File Windows vuoto: {0}',
                             'en': 'Empty Windows file: {0}',
                             'fr': 'Fichier Windows vide : {0}',
                             'de': 'Leere Windows-Datei: {0}',
                             'es': 'Archivo de Windows vacío: {0}'},
 'File exceeds the FAT32 limit: {0}. Only install.wim can be split.': {'it': 'File oltre il limite FAT32: '
                                                                             '{0}. È supportato lo split di '
                                                                             'install.wim.',
                                                                       'en': 'File exceeds the FAT32 limit: '
                                                                             '{0}. Only install.wim can be '
                                                                             'split.',
                                                                       'fr': 'Le fichier dépasse la limite '
                                                                             'FAT32 : {0}. Seul install.wim '
                                                                             'peut être fractionné.',
                                                                       'de': 'Datei überschreitet die '
                                                                             'FAT32-Grenze: {0}. Nur '
                                                                             'install.wim kann aufgeteilt '
                                                                             'werden.',
                                                                       'es': 'El archivo supera el límite '
                                                                             'FAT32: {0}. Solo se puede '
                                                                             'dividir install.wim.'},
 'ISOs with existing .swm files are not supported in this version.': {'it': 'ISO con file .swm preesistenti '
                                                                            'non supportata in questa '
                                                                            'versione.',
                                                                      'en': 'ISOs with existing .swm files '
                                                                            'are not supported in this '
                                                                            'version.',
                                                                      'fr': 'Les ISO contenant déjà des '
                                                                            'fichiers .swm ne sont pas '
                                                                            'prises en charge.',
                                                                      'de': 'ISOs mit vorhandenen '
                                                                            '.swm-Dateien werden in dieser '
                                                                            'Version nicht unterstützt.',
                                                                      'es': 'Esta versión no admite ISO con '
                                                                            'archivos .swm existentes.'},
 'Link or special file in the image: {0}': {'it': "Collegamento o file speciale nell'immagine: {0}",
                                            'en': 'Link or special file in the image: {0}',
                                            'fr': 'Lien ou fichier spécial dans l’image : {0}',
                                            'de': 'Verknüpfung oder Spezialdatei im Abbild: {0}',
                                            'es': 'Enlace o archivo especial en la imagen: {0}'},
 'This ISO is not recognized as USB hybrid. No data was written.': {'it': 'Questa ISO non è riconosciuta '
                                                                          'come ibrida USB. Nessun dato '
                                                                          'scritto.',
                                                                    'en': 'This ISO is not recognized as USB '
                                                                          'hybrid. No data was written.',
                                                                    'fr': 'Cette ISO n’est pas reconnue '
                                                                          'comme hybride USB. Aucune donnée '
                                                                          'écrite.',
                                                                    'de': 'Diese ISO wird nicht als '
                                                                          'USB-Hybrid erkannt. Es wurden '
                                                                          'keine Daten geschrieben.',
                                                                    'es': 'Esta ISO no se reconoce como '
                                                                          'híbrida USB. No se han escrito '
                                                                          'datos.'},
 'Device removed, changed or unsafe. Refresh the list.': {'it': 'Dispositivo rimosso, cambiato o non sicuro. '
                                                                "Aggiorna l'elenco.",
                                                          'en': 'Device removed, changed or unsafe. Refresh '
                                                                'the list.',
                                                          'fr': 'Périphérique retiré, modifié ou non sûr. '
                                                                'Actualisez la liste.',
                                                          'de': 'Gerät entfernt, geändert oder unsicher. '
                                                                'Liste aktualisieren.',
                                                          'es': 'Dispositivo retirado, cambiado o no seguro. '
                                                                'Actualiza la lista.'},
 'The device contains the source image.': {'it': "Il dispositivo contiene l'immagine sorgente.",
                                           'en': 'The device contains the source image.',
                                           'fr': 'Le périphérique contient l’image source.',
                                           'de': 'Das Gerät enthält das Quellabbild.',
                                           'es': 'El dispositivo contiene la imagen de origen.'},
 'Unmount all device partitions first.': {'it': 'Smonta prima tutte le partizioni del dispositivo.',
                                          'en': 'Unmount all device partitions first.',
                                          'fr': 'Démontez d’abord toutes les partitions du périphérique.',
                                          'de': 'Zuerst alle Partitionen des Geräts aushängen.',
                                          'es': 'Desmonta primero todas las particiones del dispositivo.'},
 'The device is too small for this image.': {'it': "Dispositivo troppo piccolo per l'immagine.",
                                             'en': 'The device is too small for this image.',
                                             'fr': 'Le périphérique est trop petit pour cette image.',
                                             'de': 'Das Gerät ist für dieses Abbild zu klein.',
                                             'es': 'El dispositivo es demasiado pequeño para esta imagen.'},
 'Operation cancelled: the media may be incomplete.': {'it': 'Operazione annullata: il supporto può essere '
                                                             'incompleto.',
                                                       'en': 'Operation cancelled: the media may be '
                                                             'incomplete.',
                                                       'fr': 'Opération annulée : le support peut être '
                                                             'incomplet.',
                                                       'de': 'Vorgang abgebrochen: Das Medium ist '
                                                             'möglicherweise unvollständig.',
                                                       'es': 'Operación cancelada: el medio puede estar '
                                                             'incompleto.'},
 'The source is shorter than expected.': {'it': 'La sorgente è più corta del previsto.',
                                          'en': 'The source is shorter than expected.',
                                          'fr': 'La source est plus courte que prévu.',
                                          'de': 'Die Quelle ist kürzer als erwartet.',
                                          'es': 'El origen es más corto de lo esperado.'},
 'Incomplete write to the device.': {'it': 'Scrittura incompleta sul dispositivo.',
                                     'en': 'Incomplete write to the device.',
                                     'fr': 'Écriture incomplète sur le périphérique.',
                                     'de': 'Unvollständiger Schreibvorgang auf dem Gerät.',
                                     'es': 'Escritura incompleta en el dispositivo.'},
 'The source changed during copying.': {'it': 'La sorgente è cambiata durante la copia.',
                                        'en': 'The source changed during copying.',
                                        'fr': 'La source a changé pendant la copie.',
                                        'de': 'Die Quelle wurde während des Kopierens geändert.',
                                        'es': 'El origen ha cambiado durante la copia.'},
 'Incomplete device readback.': {'it': 'Rilettura incompleta del dispositivo.',
                                 'en': 'Incomplete device readback.',
                                 'fr': 'Relecture incomplète du périphérique.',
                                 'de': 'Unvollständiges Zurücklesen des Geräts.',
                                 'es': 'Lectura de verificación incompleta del dispositivo.'},
 'Verification failed: readback data differs from the source.': {'it': 'Verifica fallita: i dati riletti '
                                                                       'sono diversi dalla sorgente.',
                                                                 'en': 'Verification failed: readback data '
                                                                       'differs from the source.',
                                                                 'fr': 'Échec de vérification : les données '
                                                                       'relues diffèrent de la source.',
                                                                 'de': 'Überprüfung fehlgeschlagen: Gelesene '
                                                                       'Daten weichen von der Quelle ab.',
                                                                 'es': 'Verificación fallida: los datos '
                                                                       'leídos difieren del origen.'},
 'The device is no longer available in UDisks2.': {'it': 'Dispositivo non più presente in UDisks2.',
                                                   'en': 'The device is no longer available in UDisks2.',
                                                   'fr': 'Le périphérique n’est plus disponible dans '
                                                         'UDisks2.',
                                                   'de': 'Das Gerät ist in UDisks2 nicht mehr verfügbar.',
                                                   'es': 'El dispositivo ya no está disponible en UDisks2.'},
 'Mount operation did not complete.': {'it': 'Montaggio non completato.',
                                       'en': 'Mount operation did not complete.',
                                       'fr': 'Le montage n’a pas abouti.',
                                       'de': 'Einhängen nicht abgeschlossen.',
                                       'es': 'No se ha completado el montaje.'},
 'Device not ready: ': {'it': 'Il dispositivo non è pronto: ',
                        'en': 'Device not ready: ',
                        'fr': 'Périphérique non prêt : ',
                        'de': 'Gerät nicht bereit: ',
                        'es': 'Dispositivo no preparado: '},
 'Invalid relative path.': {'it': 'Percorso relativo non valido.',
                            'en': 'Invalid relative path.',
                            'fr': 'Chemin relatif invalide.',
                            'de': 'Ungültiger relativer Pfad.',
                            'es': 'Ruta relativa no válida.'},
 'The path crosses into another filesystem.': {'it': 'Il percorso attraversa un altro filesystem.',
                                               'en': 'The path crosses into another filesystem.',
                                               'fr': 'Le chemin traverse un autre système de fichiers.',
                                               'de': 'Der Pfad führt in ein anderes Dateisystem.',
                                               'es': 'La ruta atraviesa otro sistema de archivos.'},
 'The destination filesystem changed.': {'it': 'Il filesystem di destinazione è cambiato.',
                                         'en': 'The destination filesystem changed.',
                                         'fr': 'Le système de fichiers de destination a changé.',
                                         'de': 'Das Zieldateisystem wurde geändert.',
                                         'es': 'El sistema de archivos de destino ha cambiado.'},
 'Size mismatch during verification: ': {'it': 'Dimensione diversa durante la verifica: ',
                                         'en': 'Size mismatch during verification: ',
                                         'fr': 'Taille différente lors de la vérification : ',
                                         'de': 'Abweichende Größe bei der Überprüfung: ',
                                         'es': 'Tamaño diferente durante la verificación: '},
 'Preparation cancelled.': {'it': 'Preparazione annullata.',
                            'en': 'Preparation cancelled.',
                            'fr': 'Préparation annulée.',
                            'de': 'Vorbereitung abgebrochen.',
                            'es': 'Preparación cancelada.'},
 'Command failed: ': {'it': 'Comando fallito: ',
                      'en': 'Command failed: ',
                      'fr': 'Échec de la commande : ',
                      'de': 'Befehl fehlgeschlagen: ',
                      'es': 'Comando fallido: '},
 'Select a non-empty regular image file.': {'it': "Seleziona un'immagine non vuota e regolare.",
                                            'en': 'Select a non-empty regular image file.',
                                            'fr': 'Sélectionnez un fichier image ordinaire non vide.',
                                            'de': 'Eine nicht leere reguläre Abbilddatei auswählen.',
                                            'es': 'Selecciona un archivo de imagen normal y no vacío.'},
 'Inspecting ISO contents…': {'it': 'Analisi del contenuto ISO…',
                              'en': 'Inspecting ISO contents…',
                              'fr': 'Analyse du contenu ISO…',
                              'de': 'ISO-Inhalt wird geprüft…',
                              'es': 'Analizando el contenido de la ISO…'},
 'Supported formats: uncompressed ISO, IMG, RAW and BIN.': {'it': 'Formati supportati: ISO, IMG, RAW e BIN '
                                                                  'non compressi.',
                                                            'en': 'Supported formats: uncompressed ISO, IMG, '
                                                                  'RAW and BIN.',
                                                            'fr': 'Formats pris en charge : ISO, IMG, RAW et '
                                                                  'BIN non compressés.',
                                                            'de': 'Unterstützte Formate: unkomprimierte ISO, '
                                                                  'IMG, RAW und BIN.',
                                                            'es': 'Formatos admitidos: ISO, IMG, RAW y BIN '
                                                                  'sin comprimir.'},
 'Windows support requires wimtools (wimlib-imagex).': {'it': 'Per Windows occorre il pacchetto wimtools '
                                                              '(wimlib-imagex).',
                                                        'en': 'Windows support requires wimtools '
                                                              '(wimlib-imagex).',
                                                        'fr': 'La prise en charge de Windows nécessite '
                                                              'wimtools (wimlib-imagex).',
                                                        'de': 'Für Windows wird wimtools (wimlib-imagex) '
                                                              'benötigt.',
                                                        'es': 'Windows requiere wimtools (wimlib-imagex).'},
 'Checking Windows file integrity…': {'it': 'Controllo integrità dei file Windows…',
                                      'en': 'Checking Windows file integrity…',
                                      'fr': 'Vérification de l’intégrité des fichiers Windows…',
                                      'de': 'Integrität der Windows-Dateien wird geprüft…',
                                      'es': 'Comprobando la integridad de los archivos de Windows…'},
 'Splitting install.wim for FAT32…': {'it': 'Suddivisione install.wim per FAT32…',
                                      'en': 'Splitting install.wim for FAT32…',
                                      'fr': 'Fractionnement de install.wim pour FAT32…',
                                      'de': 'install.wim wird für FAT32 aufgeteilt…',
                                      'es': 'Dividiendo install.wim para FAT32…'},
 'Not enough local cache space to split install.wim.': {'it': 'Spazio insufficiente nella cache locale per '
                                                              'suddividere install.wim.',
                                                        'en': 'Not enough local cache space to split '
                                                              'install.wim.',
                                                        'fr': 'Espace insuffisant dans le cache local pour '
                                                              'fractionner install.wim.',
                                                        'de': 'Nicht genug lokaler Cache-Speicher zum '
                                                              'Aufteilen von install.wim.',
                                                        'es': 'No hay espacio suficiente en la caché local '
                                                              'para dividir install.wim.'},
 'The WIM cannot be split into FAT32-compatible files.': {'it': 'Il WIM non può essere suddiviso in file '
                                                                'compatibili con FAT32.',
                                                          'en': 'The WIM cannot be split into '
                                                                'FAT32-compatible files.',
                                                          'fr': 'Le WIM ne peut pas être fractionné en '
                                                                'fichiers compatibles FAT32.',
                                                          'de': 'Das WIM lässt sich nicht in '
                                                                'FAT32-kompatible Dateien aufteilen.',
                                                          'es': 'El WIM no se puede dividir en archivos '
                                                                'compatibles con FAT32.'},
 'The source image changed. Select it again.': {'it': "L'immagine sorgente è cambiata. Selezionala "
                                                      'nuovamente.',
                                                'en': 'The source image changed. Select it again.',
                                                'fr': 'L’image source a changé. Sélectionnez-la à nouveau.',
                                                'de': 'Das Quellabbild wurde geändert. Bitte erneut '
                                                      'auswählen.',
                                                'es': 'La imagen de origen ha cambiado. Selecciónala de '
                                                      'nuevo.'},
 'The device identity changed.': {'it': "L'identità del dispositivo è cambiata.",
                                  'en': 'The device identity changed.',
                                  'fr': 'L’identité du périphérique a changé.',
                                  'de': 'Die Geräteidentität wurde geändert.',
                                  'es': 'La identidad del dispositivo ha cambiado.'},
 'Invalid device descriptor.': {'it': 'Descrittore dispositivo non valido.',
                                'en': 'Invalid device descriptor.',
                                'fr': 'Descripteur de périphérique invalide.',
                                'de': 'Ungültiger Gerätedeskriptor.',
                                'es': 'Descriptor de dispositivo no válido.'},
 'Writing': {'it': 'Scrittura', 'en': 'Writing', 'fr': 'Écriture', 'de': 'Schreiben', 'es': 'Escritura'},
 'Verifying': {'it': 'Verifica',
               'en': 'Verifying',
               'fr': 'Vérification',
               'de': 'Überprüfung',
               'es': 'Verificación'},
 'Preparing Windows UEFI': {'it': 'Preparazione Windows UEFI',
                            'en': 'Preparing Windows UEFI',
                            'fr': 'Préparation de Windows UEFI',
                            'de': 'Windows UEFI wird vorbereitet',
                            'es': 'Preparando Windows UEFI'},
 'The mounted filesystem does not match the created partition.': {'it': 'Il filesystem montato non '
                                                                        'corrisponde alla partizione creata.',
                                                                  'en': 'The mounted filesystem does not '
                                                                        'match the created partition.',
                                                                  'fr': 'Le système monté ne correspond pas '
                                                                        'à la partition créée.',
                                                                  'de': 'Das eingehängte Dateisystem '
                                                                        'entspricht nicht der erstellten '
                                                                        'Partition.',
                                                                  'es': 'El sistema montado no corresponde a '
                                                                        'la partición creada.'},
 'Not enough FAT32 space after formatting.': {'it': 'Spazio FAT32 insufficiente dopo la formattazione.',
                                              'en': 'Not enough FAT32 space after formatting.',
                                              'fr': 'Espace FAT32 insuffisant après formatage.',
                                              'de': 'Nicht genug FAT32-Speicher nach dem Formatieren.',
                                              'es': 'No hay espacio FAT32 suficiente tras el formateo.'},
 'The partition changed during verification.': {'it': 'La partizione è cambiata durante la verifica.',
                                                'en': 'The partition changed during verification.',
                                                'fr': 'La partition a changé pendant la vérification.',
                                                'de': 'Die Partition wurde während der Überprüfung geändert.',
                                                'es': 'La partición ha cambiado durante la verificación.'},
 'Copying Windows': {'it': 'Copia Windows',
                     'en': 'Copying Windows',
                     'fr': 'Copie de Windows',
                     'de': 'Windows wird kopiert',
                     'es': 'Copiando Windows'},
 'Verifying Windows': {'it': 'Verifica Windows',
                       'en': 'Verifying Windows',
                       'fr': 'Vérification de Windows',
                       'de': 'Windows wird überprüft',
                       'es': 'Verificando Windows'},
 'Linux and Windows · {0}': {'it': 'Linux e Windows · {0}',
                             'en': 'Linux and Windows · {0}',
                             'fr': 'Linux et Windows · {0}',
                             'de': 'Linux und Windows · {0}',
                             'es': 'Linux y Windows · {0}'},
 'Create a bootable USB in three steps.': {'it': 'Crea una USB avviabile, in tre passaggi.',
                                           'en': 'Create a bootable USB in three steps.',
                                           'fr': 'Créez une clé USB amorçable en trois étapes.',
                                           'de': 'In drei Schritten einen startfähigen USB-Stick erstellen.',
                                           'es': 'Crea un USB de arranque en tres pasos.'},
 '1. Choose _image…': {'it': '1. Scegli _immagine…',
                       'en': '1. Choose _image…',
                       'fr': '1. Choisir l’_image…',
                       'de': '1. _Abbild auswählen…',
                       'es': '1. Elegir _imagen…'},
 'Linux/Windows ISO, or IMG, RAW and BIN.': {'it': 'ISO Linux/Windows oppure IMG, RAW e BIN.',
                                             'en': 'Linux/Windows ISO, or IMG, RAW and BIN.',
                                             'fr': 'ISO Linux/Windows, ou IMG, RAW et BIN.',
                                             'de': 'Linux-/Windows-ISO oder IMG, RAW und BIN.',
                                             'es': 'ISO de Linux/Windows, o IMG, RAW y BIN.'},
 '2. USB/SD device': {'it': '2. Dispositivo USB/SD',
                      'en': '2. USB/SD device',
                      'fr': '2. Périphérique USB/SD',
                      'de': '2. USB-/SD-Gerät',
                      'es': '2. Dispositivo USB/SD'},
 '_Refresh': {'it': '_Aggiorna',
              'en': '_Refresh',
              'fr': '_Actualiser',
              'de': 'A_ktualisieren',
              'es': '_Actualizar'},
 'Internal disks and devices used by the system are excluded.': {'it': 'I dischi interni e quelli in uso dal '
                                                                       'sistema sono esclusi.',
                                                                 'en': 'Internal disks and devices used by '
                                                                       'the system are excluded.',
                                                                 'fr': 'Les disques internes et ceux '
                                                                       'utilisés par le système sont exclus.',
                                                                 'de': 'Interne und vom System verwendete '
                                                                       'Datenträger sind ausgeschlossen.',
                                                                 'es': 'Se excluyen los discos internos y '
                                                                       'los utilizados por el sistema.'},
 '_Unmount partitions': {'it': '_Smonta partizioni',
                         'en': '_Unmount partitions',
                         'fr': '_Démonter les partitions',
                         'de': 'Partitionen aus_hängen',
                         'es': '_Desmontar particiones'},
 '_Eject': {'it': '_Espelli', 'en': '_Eject', 'fr': '_Éjecter', 'de': '_Auswerfen', 'es': '_Expulsar'},
 'Select an image to begin.': {'it': "Seleziona un'immagine per iniziare.",
                               'en': 'Select an image to begin.',
                               'fr': 'Sélectionnez une image pour commencer.',
                               'de': 'Zum Starten ein Abbild auswählen.',
                               'es': 'Selecciona una imagen para empezar.'},
 '_Cancel': {'it': 'A_nnulla', 'en': '_Cancel', 'fr': 'A_nnuler', 'de': 'Ab_brechen', 'es': 'Ca_ncelar'},
 '3. _Write and verify': {'it': '3. _Scrivi e verifica',
                          'en': '3. _Write and verify',
                          'fr': '3. _Écrire et vérifier',
                          'de': '3. _Schreiben und prüfen',
                          'es': '3. _Escribir y verificar'},
 'Writing erases the selected device. No persistence.': {'it': 'La scrittura cancella il dispositivo '
                                                               'selezionato. Nessuna persistenza.',
                                                         'en': 'Writing erases the selected device. No '
                                                               'persistence.',
                                                         'fr': 'L’écriture efface le périphérique '
                                                               'sélectionné. Sans persistance.',
                                                         'de': 'Das Schreiben löscht das ausgewählte Gerät. '
                                                               'Keine Persistenz.',
                                                         'es': 'La escritura borra el dispositivo '
                                                               'seleccionado. Sin persistencia.'},
 'Operation not completed': {'it': 'Operazione non completata',
                             'en': 'Operation not completed',
                             'fr': 'Opération non terminée',
                             'de': 'Vorgang nicht abgeschlossen',
                             'es': 'Operación no completada'},
 'Choose image': {'it': 'Scegli immagine',
                  'en': 'Choose image',
                  'fr': 'Choisir une image',
                  'de': 'Abbild auswählen',
                  'es': 'Elegir imagen'},
 'Cancel': {'it': 'Annulla', 'en': 'Cancel', 'fr': 'Annuler', 'de': 'Abbrechen', 'es': 'Cancelar'},
 'Open': {'it': 'Apri', 'en': 'Open', 'fr': 'Ouvrir', 'de': 'Öffnen', 'es': 'Abrir'},
 'ISO, IMG, RAW and BIN images': {'it': 'Immagini ISO, IMG, RAW e BIN',
                                  'en': 'ISO, IMG, RAW and BIN images',
                                  'fr': 'Images ISO, IMG, RAW et BIN',
                                  'de': 'ISO-, IMG-, RAW- und BIN-Abbilder',
                                  'es': 'Imágenes ISO, IMG, RAW y BIN'},
 'Windows · UEFI x64': {'it': 'Windows · UEFI x64',
                        'en': 'Windows · UEFI x64',
                        'fr': 'Windows · UEFI x64',
                        'de': 'Windows · UEFI x64',
                        'es': 'Windows · UEFI x64'},
 'Linux / raw image': {'it': 'Linux / immagine raw',
                       'en': 'Linux / raw image',
                       'fr': 'Linux / image brute',
                       'de': 'Linux / Rohabbild',
                       'es': 'Linux / imagen raw'},
 '{0}\n{1} · at least {2}': {'it': '{0}\n{1} · almeno {2}',
                             'en': '{0}\n{1} · at least {2}',
                             'fr': '{0}\n{1} · au moins {2}',
                             'de': '{0}\n{1} · mindestens {2}',
                             'es': '{0}\n{1} · al menos {2}'},
 'Image ready. Select the device and unmount its partitions.': {'it': 'Immagine pronta. Seleziona il '
                                                                      'dispositivo e smonta le sue '
                                                                      'partizioni.',
                                                                'en': 'Image ready. Select the device and '
                                                                      'unmount its partitions.',
                                                                'fr': 'Image prête. Sélectionnez le '
                                                                      'périphérique et démontez ses '
                                                                      'partitions.',
                                                                'de': 'Abbild bereit. Gerät auswählen und '
                                                                      'dessen Partitionen aushängen.',
                                                                'es': 'Imagen lista. Selecciona el '
                                                                      'dispositivo y desmonta sus '
                                                                      'particiones.'},
 'Inspecting image…': {'it': "Analisi dell'immagine…",
                       'en': 'Inspecting image…',
                       'fr': 'Analyse de l’image…',
                       'de': 'Abbild wird geprüft…',
                       'es': 'Analizando la imagen…'},
 'Preparing image…': {'it': 'Preparazione immagine…',
                      'en': 'Preparing image…',
                      'fr': 'Préparation de l’image…',
                      'de': 'Abbild wird vorbereitet…',
                      'es': 'Preparando la imagen…'},
 'No usable USB/SD device. Connect the media and refresh.': {'it': 'Nessun dispositivo USB/SD utilizzabile. '
                                                                   'Collega il supporto e aggiorna.',
                                                             'en': 'No usable USB/SD device. Connect the '
                                                                   'media and refresh.',
                                                             'fr': 'Aucun périphérique USB/SD utilisable. '
                                                                   'Connectez le support et actualisez.',
                                                             'de': 'Kein verwendbares USB-/SD-Gerät. Medium '
                                                                   'anschließen und aktualisieren.',
                                                             'es': 'No hay USB/SD utilizables. Conecta el '
                                                                   'medio y actualiza.'},
 'Check the model, capacity and path before writing.': {'it': 'Controlla modello, capacità e percorso prima '
                                                              'di scrivere.',
                                                        'en': 'Check the model, capacity and path before '
                                                              'writing.',
                                                        'fr': 'Vérifiez le modèle, la capacité et le chemin '
                                                              'avant d’écrire.',
                                                        'de': 'Vor dem Schreiben Modell, Kapazität und Pfad '
                                                              'prüfen.',
                                                        'es': 'Comprueba modelo, capacidad y ruta antes de '
                                                              'escribir.'},
 'Ready.': {'it': 'Pronto.', 'en': 'Ready.', 'fr': 'Prêt.', 'de': 'Bereit.', 'es': 'Listo.'},
 'Scanning devices…': {'it': 'Ricerca dispositivi…',
                       'en': 'Scanning devices…',
                       'fr': 'Recherche de périphériques…',
                       'de': 'Geräte werden gesucht…',
                       'es': 'Buscando dispositivos…'},
 'Device changed or unsafe.': {'it': 'Dispositivo cambiato o non sicuro.',
                               'en': 'Device changed or unsafe.',
                               'fr': 'Périphérique modifié ou non sûr.',
                               'de': 'Gerät geändert oder unsicher.',
                               'es': 'Dispositivo cambiado o no seguro.'},
 'This device contains the source image.': {'it': "Questo dispositivo contiene l'immagine sorgente.",
                                            'en': 'This device contains the source image.',
                                            'fr': 'Ce périphérique contient l’image source.',
                                            'de': 'Dieses Gerät enthält das Quellabbild.',
                                            'es': 'Este dispositivo contiene la imagen de origen.'},
 'Partitions unmounted. You can start writing.': {'it': 'Partizioni smontate. Puoi avviare la scrittura.',
                                                  'en': 'Partitions unmounted. You can start writing.',
                                                  'fr': 'Partitions démontées. Vous pouvez lancer '
                                                        'l’écriture.',
                                                  'de': 'Partitionen ausgehängt. Das Schreiben kann '
                                                        'beginnen.',
                                                  'es': 'Particiones desmontadas. Puedes iniciar la '
                                                        'escritura.'},
 'Unmounting partitions…': {'it': 'Smontaggio partizioni…',
                            'en': 'Unmounting partitions…',
                            'fr': 'Démontage des partitions…',
                            'de': 'Partitionen werden ausgehängt…',
                            'es': 'Desmontando particiones…'},
 'Unmount partitions before ejecting the device.': {'it': 'Smonta le partizioni prima di espellere il '
                                                          'dispositivo.',
                                                    'en': 'Unmount partitions before ejecting the device.',
                                                    'fr': 'Démontez les partitions avant d’éjecter le '
                                                          'périphérique.',
                                                    'de': 'Vor dem Auswerfen die Partitionen aushängen.',
                                                    'es': 'Desmonta las particiones antes de expulsar el '
                                                          'dispositivo.'},
 'Ejection unavailable: unmounted media can be removed.': {'it': 'Espulsione non disponibile: le partizioni '
                                                                 'smontate possono essere rimosse.',
                                                           'en': 'Ejection unavailable: unmounted media can '
                                                                 'be removed.',
                                                           'fr': 'Éjection indisponible : le support démonté '
                                                                 'peut être retiré.',
                                                           'de': 'Auswerfen nicht verfügbar: Ausgehängte '
                                                                 'Medien können entfernt werden.',
                                                           'es': 'Expulsión no disponible: puedes retirar el '
                                                                 'medio desmontado.'},
 'Ejecting…': {'it': 'Espulsione…',
               'en': 'Ejecting…',
               'fr': 'Éjection…',
               'de': 'Medium wird ausgeworfen…',
               'es': 'Expulsando…'},
 'Confirm erasure': {'it': 'Conferma cancellazione',
                     'en': 'Confirm erasure',
                     'fr': 'Confirmer l’effacement',
                     'de': 'Löschen bestätigen',
                     'es': 'Confirmar borrado'},
 'Erase and write': {'it': 'Cancella e scrivi',
                     'en': 'Erase and write',
                     'fr': 'Effacer et écrire',
                     'de': 'Löschen und schreiben',
                     'es': 'Borrar y escribir'},
 'All data on {0} will be erased.\n{1} · {2} · {3}\n\nTo confirm, type {4}:': {'it': 'Tutti i dati su {0} '
                                                                                     'verranno cancellati.\n'
                                                                                     '{1} · {2} · {3}\n'
                                                                                     '\n'
                                                                                     'Per confermare, digita '
                                                                                     '{4}:',
                                                                               'en': 'All data on {0} will '
                                                                                     'be erased.\n'
                                                                                     '{1} · {2} · {3}\n'
                                                                                     '\n'
                                                                                     'To confirm, type {4}:',
                                                                               'fr': 'Toutes les données sur '
                                                                                     '{0} seront effacées.\n'
                                                                                     '{1} · {2} · {3}\n'
                                                                                     '\n'
                                                                                     'Pour confirmer, '
                                                                                     'saisissez {4} :',
                                                                               'de': 'Alle Daten auf {0} '
                                                                                     'werden gelöscht.\n'
                                                                                     '{1} · {2} · {3}\n'
                                                                                     '\n'
                                                                                     'Zur Bestätigung {4} '
                                                                                     'eingeben:',
                                                                               'es': 'Se borrarán todos los '
                                                                                     'datos de {0}.\n'
                                                                                     '{1} · {2} · {3}\n'
                                                                                     '\n'
                                                                                     'Para confirmar, '
                                                                                     'escribe {4}:'},
 'Device path to erase': {'it': 'Percorso del dispositivo da cancellare',
                          'en': 'Device path to erase',
                          'fr': 'Chemin du périphérique à effacer',
                          'de': 'Pfad des zu löschenden Geräts',
                          'es': 'Ruta del dispositivo que se borrará'},
 'Writing and verification complete. You can eject the device.': {'it': 'Scrittura e verifica completate. '
                                                                        'Puoi espellere il dispositivo.',
                                                                  'en': 'Writing and verification complete. '
                                                                        'You can eject the device.',
                                                                  'fr': 'Écriture et vérification terminées. '
                                                                        'Vous pouvez éjecter le '
                                                                        'périphérique.',
                                                                  'de': 'Schreiben und Überprüfung '
                                                                        'abgeschlossen. Das Gerät kann '
                                                                        'ausgeworfen werden.',
                                                                  'es': 'Escritura y verificación '
                                                                        'completadas. Puedes expulsar el '
                                                                        'dispositivo.'},
 'Final device check…': {'it': 'Controllo finale dispositivo…',
                         'en': 'Final device check…',
                         'fr': 'Dernière vérification du périphérique…',
                         'de': 'Letzte Geräteprüfung…',
                         'es': 'Comprobación final del dispositivo…'},
 'Cancellation requested. Wait for the current operation to finish…': {'it': 'Annullamento richiesto. '
                                                                             'Attendi il completamento '
                                                                             "dell'operazione in corso…",
                                                                       'en': 'Cancellation requested. Wait '
                                                                             'for the current operation to '
                                                                             'finish…',
                                                                       'fr': 'Annulation demandée. Attendez '
                                                                             'la fin de l’opération en '
                                                                             'cours…',
                                                                       'de': 'Abbruch angefordert. Bitte den '
                                                                             'laufenden Vorgang abwarten…',
                                                                       'es': 'Cancelación solicitada. Espera '
                                                                             'a que termine la operación '
                                                                             'actual…'},
 'Releasing image…': {'it': 'Rilascio immagine…',
                      'en': 'Releasing image…',
                      'fr': 'Libération de l’image…',
                      'de': 'Abbild wird freigegeben…',
                      'es': 'Liberando imagen…'},
 'Run DistroFlash as a normal user: Polkit manages permissions.': {'it': 'Avvia DistroFlash come utente '
                                                                         'normale: Polkit gestisce i '
                                                                         'permessi.',
                                                                   'en': 'Run DistroFlash as a normal user: '
                                                                         'Polkit manages permissions.',
                                                                   'fr': 'Lancez DistroFlash en utilisateur '
                                                                         'normal : Polkit gère les '
                                                                         'autorisations.',
                                                                   'de': 'DistroFlash als normaler Benutzer '
                                                                         'starten: Polkit verwaltet die '
                                                                         'Berechtigungen.',
                                                                   'es': 'Ejecuta DistroFlash como usuario '
                                                                         'normal: Polkit gestiona los '
                                                                         'permisos.'},
 'DistroFlash — Linux and Windows USB': {'it': 'DistroFlash — USB Linux e Windows',
                                         'en': 'DistroFlash — Linux and Windows USB',
                                         'fr': 'DistroFlash — USB Linux et Windows',
                                         'de': 'DistroFlash — Linux- und Windows-USB',
                                         'es': 'DistroFlash — USB de Linux y Windows'},
 'list usable USB/SD devices without making changes': {'it': 'elenca USB/SD utilizzabili, senza modifiche',
                                                       'en': 'list usable USB/SD devices without making '
                                                             'changes',
                                                       'fr': 'lister les périphériques USB/SD utilisables '
                                                             'sans modification',
                                                       'de': 'verwendbare USB-/SD-Geräte ohne Änderungen '
                                                             'auflisten',
                                                       'es': 'listar dispositivos USB/SD utilizables sin '
                                                             'realizar cambios'}}

MESSAGES["The created filesystem is not FAT32. No Windows files were copied."] = {
    "en": "The created filesystem is not FAT32. No Windows files were copied.",
    "it": "Il filesystem creato non è FAT32. Nessun file Windows è stato copiato.",
    "fr": "Le système créé n’est pas FAT32. Aucun fichier Windows n’a été copié.",
    "de": "Das erstellte Dateisystem ist nicht FAT32. Es wurden keine Windows-Dateien kopiert.",
    "es": "El sistema creado no es FAT32. No se han copiado archivos de Windows.",
}


MESSAGES.update({
    'Checking Windows image metadata…': {
        'en': 'Checking Windows image metadata…',
        'it': 'Controllo metadati immagine Windows…',
        'fr': 'Vérification des métadonnées de l’image Windows…',
        'de': 'Metadaten des Windows-Abbilds werden geprüft…',
        'es': 'Comprobando los metadatos de la imagen de Windows…',
    },
    '_Deep Windows integrity check (slower)': {
        'en': '_Deep Windows integrity check (slower)',
        'it': 'Controllo _approfondito integrità Windows (più lento)',
        'fr': 'Vérification _approfondie de l’intégrité Windows (plus lente)',
        'de': '_Gründliche Windows-Integritätsprüfung (langsamer)',
        'es': 'Comprobación _exhaustiva de integridad de Windows (más lenta)',
    },
    'Fully decompress and check Windows archives before writing. Written USB files are always verified.': {
        'en': 'Fully decompress and check Windows archives before writing. Written USB files are always verified.',
        'it': 'Decomprime e controlla tutti gli archivi Windows prima della scrittura. I file scritti sulla USB vengono sempre verificati.',
        'fr': 'Décompresse et vérifie entièrement les archives Windows avant l’écriture. Les fichiers écrits sur la clé USB sont toujours vérifiés.',
        'de': 'Windows-Archive vor dem Schreiben vollständig dekomprimieren und prüfen. Geschriebene USB-Dateien werden immer überprüft.',
        'es': 'Descomprime y comprueba todos los archivos de Windows antes de escribir. Los archivos escritos en la USB siempre se verifican.',
    },
})
