from flask import Flask,render_template,redirect,request,url_for
from flask import current_app as app
from .models import *
from sqlalchemy import or_,and_
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
def raw(text):
    split_list=text.split()
    src_wrd=''
    for word in split_list:
        src_wrd+=word.lower()
    return src_wrd
@app.route('/')
def mainpage_login():
    return render_template('mainpage.html')


@app.route('/userlogin',methods=['POST','GET'])
def user_login():
    if(request.method=='POST'):
        u_name=request.form.get("uname")
        pwd=request.form.get("pwd")
        duname=User.query.filter_by(username=u_name).first()
        if(duname):
            if(duname.password==pwd):
                return redirect(f'/user/{duname.id}')
            else:
                return render_template("incorrectpwd.html")
        else:
            return render_template("incorrectuser.html")
    else:
        return render_template("login.html")

@app.route("/user_register",methods=["POST","GET"])
def user_register():
    if(request.method=='POST'):
        u_name=request.form.get("uname")
        pwd=request.form.get("pwd")
        duname=User.query.filter_by(username=u_name).first()
        if(duname):
            return render_template("useralready.html")
        else:
            new_user=User(username=u_name,password=pwd)
            db.session.add(new_user)
            db.session.commit()
            return redirect("/userlogin")

    return render_template('register.html')

@app.route("/lib_login",methods=["POST","GET"])
def librarian_login():
    if(request.method=='POST'):
        u_name=request.form.get("uname")
        pwd=request.form.get("pwd")
        duname=Admin.query.filter_by(username=u_name).first();
        if(duname):
            if(duname.password==pwd):
                return redirect("/home")
            else:
                return render_template("incorrectpwdadmin.html")
        else:
            return render_template("incorrectadmin.html")
    return render_template("liblogin.html")

@app.route("/user/<int:user_id>",methods=['POST','GET'])
def user_dashboard(user_id):
    user=User.query.get(user_id)
    books=Book.query.all()
    reqbook=UserBook.query.filter_by(uid=user_id,status="Requested").all()
    grantbook=UserBook.query.filter_by(uid=user_id,status="Granted").all()
    reqgrant=[]
    for book in reqbook:
        reqgrant.append(book.bid)
    for book in grantbook:
        reqgrant.append(book.bid)
    return render_template('Books.html',books=books,user=user,reqgrant=reqgrant)

@app.route("/home",methods=['POST','GET'])
def lib_home():
    section=Section.query.all()
    return render_template('home.html',sections=section)
@app.route("/addsection",methods=['POST','GET'])
def add_section():
    if(request.method=='POST'):
        sname=request.form.get("title")
        dcreate=request.form.get("date")
        desc=request.form.get("desc")
        img=request.form.get("img")
        new_section=Section(sname=sname,dcreate=dcreate,desc=desc,imglink=img)
        db.session.add(new_section)
        db.session.commit()
        return redirect('/home')
    else:
        return render_template('Addsection.html')
@app.route("/addbook/<int:section_id>",methods=['POST','GET'])
def add_book(section_id):
    if(request.method=='POST'):
        bname=request.form.get("title")
        content=request.form.get("content")
        author=request.form.get("author")
        img=request.form.get("img")
        temps=Section.query.filter_by(sid=section_id).first();
        new_book=Book(bname=bname,content=content,author=author,b_search_name=raw(bname+author+temps.sname),sec_id=section_id,imglink=img)
        db.session.add(new_book)
        db.session.commit()
        return redirect('/home')
    else:
        section=Section.query.get(section_id)
        return render_template('Addbooks.html',section=section)
@app.route("/viewbook/<int:sec_id>",methods=['POST','GET'])
def view_book(sec_id):
    sname=Section.query.get(sec_id).sname;
    books=Book.query.filter_by(sec_id=sec_id).all();
    grantbook=UserBook.query.filter_by(status="Granted").all()
    return render_template('viewbook.html',books=books,sname=sname)

@app.route("/<int:user_id>/search")
def search_result(user_id):
    user=User.query.get(user_id)
    srch_word=request.args.get("src_word")
    srch_word="%"+srch_word.lower()+"%"
    b_name=Book.query.filter(Book.b_search_name.like(srch_word)).all()
    reqbook=UserBook.query.filter_by(uid=user_id,status="Requested").all()
    grantbook=UserBook.query.filter_by(uid=user_id,status="Granted").all()
    reqgrant=[]
    for book in reqbook:
        reqgrant.append(book.bid)
    for book in grantbook:
        reqgrant.append(book.bid)
    return render_template('srch_result.html',b_names=b_name,user=user,reqgrant=reqgrant)
@app.route("/requestbook/<int:user_id>/<int:book_id>",methods=['POST','GET'])
def request_book(user_id,book_id):
    user=User.query.get(user_id)
    if(request.method=='POST'):
        if(user.nobooks==5):
            return redirect(f'/user/{user_id}')
        else:
            nday=request.form.get("nday")
            book=Book.query.get(book_id)
            newbookuser=UserBook(uid=user.id,bid=book.bid,nday=nday,issuedate=dt.datetime.now().date())
            user.nobooks=user.nobooks+1
            db.session.add(newbookuser)
            db.session.commit()
            return redirect(f'/user/{user_id}')
    else:
        book=Book.query.get(book_id)
        user=User.query.get(user_id)
        return render_template('requestbook.html',book=book,user=user)

@app.route("/request",methods=['POST','GET'])
def requests():
    reqs=UserBook.query.filter_by(status="Requested").all();
    #nreqs=UserBook.query.filter_by(status="Requested").all();
    grant=UserBook.query.filter_by(status="Granted").all();
    for g in grant:
        x = dt.datetime.now().date()
        rdate=x.strftime("%d/%m/%Y")
        if(g.returndate==rdate):
            g.status="completed"
            uid=User.query.get(g.uid)
            uid.nobooks=uid.nobooks-1
            db.session.commit()
    ngrant=UserBook.query.filter_by(status="Granted").all();
    return render_template('requests.html',reqs=reqs,grant=ngrant)

@app.route("/viewrequest/<int:userreq_id>",methods=['POST','GET'])
def view_request(userreq_id):
    bookreq=UserBook.query.get(userreq_id)
    return render_template('ViewRequest.html',bookreq=bookreq)
@app.route("/grantrequest/<int:userreq_id>",methods=['POST','GET'])
def grant_request(userreq_id):
    bookreq=UserBook.query.get(userreq_id)
    nday=bookreq.nday
    x = dt.datetime.now().date()
    issuedate=x.strftime("%d/%m/%Y")
    returndate=(x+dt.timedelta(days=int(nday))).strftime("%d/%m/%Y")
    bookreq.issuedate=issuedate
    bookreq.returndate=returndate
    bookreq.status="Granted"
    db.session.commit()
    return redirect('/request')

@app.route("/revoke/<int:userreq_id>",methods=['POST','GET'])
def revoke_request(userreq_id):
    revbook=UserBook.query.get(userreq_id)
    revbook.status="completed"
    user=User.query.get(revbook.uid)
    user.nobooks=user.nobooks-1
    db.session.commit()
    return redirect('/request')
@app.route("/return/<int:ind>",methods=['POST','GET'])
def return_book(ind):
    retunbook=UserBook.query.get(ind)
    retunbook.status="completed"
    user=User.query.get(retunbook.uid)
    user.nobooks=user.nobooks-1
    db.session.commit()
    return redirect("/mybooks/"+str(retunbook.uid))
@app.route("/mybooks/<int:user_id>",methods=['POST','GET'])
def mybooks(user_id):
    user=User.query.get(user_id)
    gbooks=UserBook.query.filter_by(status="Granted",uid=user_id).all();
    cbooks=books=UserBook.query.filter_by(uid=user_id,status="completed").all();
    return render_template('MyBooks.html',gbooks=gbooks,cbooks=cbooks,user=user)
@app.route("/viewmybook/<int:ind>",methods=['POST','GET'])
def view_completed_book(ind):
    vbook=UserBook.query.get(ind)
    user=User.query.get(vbook.uid)
    if(request.method=='POST'):
        rating=request.form.get("rating")
        feedback=request.form.get("feedback")
        vbook.rating=rating
        vbook.feedback=feedback
        db.session.commit()
    return render_template('bookfeedback.html',vbook=vbook,user=user)

@app.route("/updatesection/<int:section_id>",methods=['POST','GET'])
def update_section(section_id):
    section=Section.query.get(section_id)
    if(request.method=='POST'):
        if(request.form.get("title")):
            section.sname=request.form.get("title")
        if(request.form.get("date")):
            section.dcreate=request.form.get("date")
        if(request.form.get("desc")):
            section.desc=request.form.get("desc")
        db.session.commit()
        return redirect('/home')
    return render_template('updatesection.html',section=section)

@app.route("/deletesection/<int:section_id>",methods=['POST','GET'])
def delete_section(section_id):
    books=Book.query.filter_by(sec_id=section_id).all()
    section=Section.query.get(section_id)
    for book in books:
        for tuser in book.book_u:
            if(tuser.bid==book.bid):
                userid=User.query.get(tuser.uid)
                userid.nobooks=userid.nobooks-1
                db.session.delete(tuser)
        db.session.delete(book)
    db.session.delete(section)
    db.session.commit()
    return redirect('/home')

@app.route("/editbook/<int:book_id>",methods=['POST','GET'])
def edit_book(book_id):
    book=Book.query.get(book_id)
    if(request.method=='POST'):
        if(request.form.get("title")):
            book.bname=request.form.get("title")
        if(request.form.get("author")):
            book.author=request.form.get("author")
        if(request.form.get("content")):
            book.content=request.form.get("content")
        if(request.form.get("img")):
            book.imglink=request.form.get("img")
        book.b_search_name=raw(book.bname+book.author+book.book_s.sname)
        db.session.commit()
        return redirect('/home')
    return render_template('editbook.html',book=book)
@app.route("/deletebook/<int:book_id>",methods=['POST','GET'])
def delete_book(book_id):
    book=Book.query.get(book_id)
    for tuser in book.book_u:
        if(tuser.bid==book.bid):
            if(tuser.status=="Requested" or tuser.status=="Granted"):
                userid=User.query.get(tuser.uid)
                userid.nobooks=userid.nobooks-1
            db.session.delete(tuser)
            db.session.commit()
    db.session.delete(book)
    db.session.commit()
    return redirect('/home')

@app.route("/userstats/<int:user_id>",methods=['POST','GET'])
def user_stats(user_id):
    user=User.query.get(user_id)
    ubooks=UserBook.query.filter_by(uid=user_id).all()
    status=[]
    for book in ubooks:
        status.append(book.status)
    section=[]
    for tbook in ubooks:
        if(tbook.status=="completed"):
            section.append(tbook.book.book_s.sname)      
    plt.clf()
    plt.xlabel('Book Status')
    plt.ylabel('No of Books')
    plt.hist(status)
    plt.savefig("static/userstats.png")
    plt.clf()
    plt.xlabel('Section')
    plt.ylabel('No of Books')
    plt.hist(section)
    plt.savefig("static/sectiondis.png")
    return render_template('userstats.html',user=user)
@app.route("/libstats")
def lib_stats():
    ubooks=UserBook.query.filter_by().all()
    grant=[]
    request=[]
    gsection=[]
    rsection=[]
    for tbook in ubooks:
        if(tbook.status=="Granted" and tbook.bid!=None):
            grant.append(tbook.user.username)
            gsection.append(tbook.book.book_s.sname)
        elif(tbook.status=="Requested" and tbook.bid!=None):
            request.append(tbook.user.username)
            rsection.append(tbook.book.book_s.sname)
    plt.clf()
    plt.xlabel('Username')
    plt.ylabel('No of Books')
    plt.hist(grant)
    plt.savefig("static/grant.png")
    plt.clf()
    plt.xlabel('Username')
    plt.ylabel('No of Books')
    plt.hist(request)
    plt.savefig("static/request.png")
    plt.clf()
    plt.xlabel('Section')
    plt.ylabel('No of Books')
    plt.hist(gsection)
    plt.savefig("static/gsection.png")
    plt.clf()
    plt.xlabel('Section')
    plt.ylabel('No of Books')
    plt.hist(rsection)
    plt.savefig("static/rsection.png")  
    return render_template('libstats.html')
