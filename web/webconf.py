


import os 

prefix_path_template = os.path.join(os.path.dirname(__file__),'template')

path_template_homehandler = os.path.join(prefix_path_template,'home.html')
path_template_searchhandler = os.path.join(prefix_path_template,'searchres.html')
path_template_queryhandler = os.path.join(prefix_path_template,'queryres.html')
path_template_formdetail = os.path.join(prefix_path_template,'formdetail.html')
path_template_rawdetail = os.path.join(prefix_path_template,'rawdetail.html')


if __name__ == "__main__":
    print(prefix_path_template)