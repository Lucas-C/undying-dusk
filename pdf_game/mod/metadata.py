from datetime import datetime

from fpdf import FPDF_VERSION


METADATA = {
    'dc:title': 'Undying Dusk',
    'dc:description': 'PDF port of Clint Bellanger 2013 RPG dungeon crawl game',
    'dc:creator': 'Lucas Cimon',
    'pdf:Keywords': 'pdf interactive game video-game dungeon crawl',
    'pdf:Producer': f'PyFPDF/fpdf{FPDF_VERSION}',
    'xmp:CreatorTool': 'Lucas-C/undying-dusk',
    'xmp:MetadataDate': datetime.now(datetime.utcnow().astimezone().tzinfo).isoformat()
}

XMP_METADATA = f'''<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="fpdf2">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about="">
      <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">
        <rdf:Alt>
          <rdf:li xml:lang="x-default">{METADATA['dc:title']}</rdf:li>
        </rdf:Alt>
      </dc:title>
    </rdf:Description>
    <rdf:Description rdf:about="">
      <dc:description xmlns:dc="http://purl.org/dc/elements/1.1/">
        <rdf:Alt>
          <rdf:li xml:lang="x-default">{METADATA['dc:description']}</rdf:li>
        </rdf:Alt>
      </dc:description>
    </rdf:Description>
    <rdf:Description rdf:about="">
      <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">
        <rdf:Seq>
          <rdf:li>{METADATA['dc:creator']}</rdf:li>
        </rdf:Seq>
      </dc:creator>
    </rdf:Description>
    <rdf:Description xmlns:pdf="http://ns.adobe.com/pdf/1.3/" rdf:about="" pdf:Keywords="{METADATA['pdf:Keywords']}"/>
    <rdf:Description xmlns:pdf="http://ns.adobe.com/pdf/1.3/" rdf:about="" pdf:Producer="{METADATA['pdf:Producer']}"/>
    <rdf:Description xmlns:xmp="http://ns.adobe.com/xap/1.0/" rdf:about="" xmp:CreatorTool="{METADATA['xmp:CreatorTool']}"/>
    <rdf:Description xmlns:xmp="http://ns.adobe.com/xap/1.0/" rdf:about="" xmp:MetadataDate="{METADATA['xmp:MetadataDate']}"/>
  </rdf:RDF>
</x:xmpmeta>'''
