# OCR-Fixer
A scripting tool in Python to help correct and transform poor quality OCR texts 

## Why?

Repositories of scanned works, such as archive.org and Google books are fantastic resources, providing access to out of
print works in several different formats.  These include textual versions created through an optical character recognition 
(OCR) process -  however, the inevitable age and poor condition of some of the scanned works mean that the quality of the resulting text
can be quite poor with many incorrectly recognised words,  spurious markings and inconsistent layout. This can severely limit
their usefulness.

 often a first response can be to open the text file in our favourite editor and begin hacking away with global edits,
 spelling correctors, wrapping with HTML tags and a great deal of hand editing. Whilst this may give a more useful end
 result it is essentially a "one-way function" - we have no record of the changes or means to undo them or redo them
 differently.

OCR-Fixer is a tool to help with this process, think of it as a *sed* command script with an easier to read syntax,
support for multiple output and special support for wrapping content in HTML tags. For example, consider the following
extract of an OCR'd document: (Line no.s for guidance, not part of the document)

```
 1. fi&gt;t^^i&lt;^JSI-X 
 2. HERALDIC BLAZON, NOMENCLATURE, LANGUAGE, AND LAW'S. 
 3.
 4. In Heraldrj', the term Blazon, or Blazoning, is applied 
 5. equally to tlie description and to the representation of all 
 6. heraldic figures, devices, and compositions. It also indicates 
 7. the arrangement of the component members and details of any- 
 8. heraldic composition. Historical Blazoning, also entitled Mar- 
 9. shalling, denotes the combination and arrangement of several 
10. distinct heraldic compositions, with the view to produce a single 
11. compound composition. In like manner, the disposition and 
12. arrangement of a group or groups of heraldic compositions or 
13. objects, is styled Marshall iyig. 
14.
15. All heraldic figures and devices, whether placed upon shields, 
16. or borne or represented in any other manner, are entitled 
17. Charges ; and every shield or other object is said to be charged 
18. Avith the armorial insignia that may be displayed upon it. 
19.
```
When we apply the following OCR-Fixer script:
```
1 ignore
2 h1 _dataline_
& moveon

4 fix drj' dry
13 fix " iyig" ing
18 fix Avith With

* para _dataline_
```
We will obtain the following output:
```html
<h1 data-source-line="2" data-source-file="example.txt">HERALDIC BLAZON, NOMENCLATURE, LANGUAGE, AND LAW'S. 
</h1>

 <p data-source-line="4" data-source-file="example.txt"> In Heraldry, the term Blazon,
 or Blazoning, is applied equally to tlie description and to the representation of
 all heraldic figures, devices, and compositions. It also indicates the arrangement
 of the component members and details of anyheraldic composition. Historical Blazoning,
 also entitled Marshalling, denotes the combination and arrangement of several distinct
 heraldic compositions, with the view to produce a single compound composition. In
 like manner, the disposition and arrangement of a group or groups of heraldic compositions
 or objects, is styled Marshalling.</p>

 <p data-source-line="15" data-source-file="example.txt"> All heraldic figures and devices,
 whether placed upon shields, or borne or represented in any other manner, are entitled
 Charges ; and every shield or other object is said to be charged With the armorial
 insignia that may be displayed upon it.</p>
```
