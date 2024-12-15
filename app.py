from flask import *
import datetime
import sqlite3
import json

app = Flask(__name__)
app.debug = True

###### 데이터베이스 연결 ######

connect = sqlite3.connect('test.db')
connect.execute("PRAGMA foreign_keys = ON;")
Cursor = connect.cursor()

# 유저 테이블 생성 쿼리
createUserTable =  """
    CREATE TABLE IF NOT EXISTS TestUser (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track VARCHAR(32) NOT NULL,
    plan VARCHAR(10) NOT NULL,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    pw VARCHAR(255) NOT NULL,
    date DATETIME NOT NULL
    );
"""

# 체크리스트 테이블 생성 쿼리
createCheckList = """
    CREATE TABLE IF NOT EXISTS CheckList (
    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    text VARCHAR(300) NOT NULL,
    date DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES TestUser (id) ON DELETE CASCADE
    );
"""

# 게시글 테이블 생성 쿼리
createBoard = """
    CREATE TABLE IF NOT EXISTS board (
    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    user_name VARCHAR(50) NOT NULL,
    plan VARCHAR(10) NOT NULL,
    title VARCHAR(300) NOT NULL,
    text VARCHAR(65535) NOT NULL,
    date DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES TestUser (id) ON DELETE CASCADE,
    FOREIGN KEY (user_name) REFERENCES TestUser (name),
    FOREIGN KEY (plan) REFERENCES TestUser (plan)
    );
"""

# 댓글 테이블 생성 쿼리
createComment = """
    CREATE TABLE IF NOT EXISTS comment (
    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    user_name VARCHAR(50) NOT NULL,
    plan VARCHAR(10) NOT NULL,
    text VARCHAR(500) NOT NULL,
    date DATETIME NOT NULL,
    FOREIGN KEY (post_id) REFERENCES board (post_id) ON DELETE CASCADE,
    FOREIGN KEY (user_name) REFERENCES TestUser (name),
    FOREIGN KEY (plan) REFERENCES TestUser (plan)
    );
"""

# 쿼리 실행
Cursor.execute(createUserTable)
Cursor.execute(createCheckList)
Cursor.execute(createBoard)
Cursor.execute(createComment)

# 변경 사항 저장 및 연결 닫기
connect.commit()
connect.close()



##### 어플리케이션 로직 #####

# 메인 페이지 접근 처리
@app.route('/')
def index():
    cookie = request.cookies.get('user_id')
    if cookie:
        connect = sqlite3.connect('test.db')
        connect.row_factory = sqlite3.Row
        connect.execute("PRAGMA foreign_keys = ON;")
        Cursor = connect.cursor()
        selectUserInfo = f"""
            SELECT * FROM TestUser WHERE 
            id={cookie};
        """
        selectList = f"""
            SELECT post_id, text FROM CheckList WHERE
            user_id={cookie};
        """
        Cursor.execute(selectUserInfo)
        userData = Cursor.fetchone()
        track = userData['track']
        name = userData['name']
        Cursor.execute(selectList)
        checkLists = Cursor.fetchall()
        connect.commit()
        connect.close()
        return render_template('index.html', loginState=True ,track=track, name=name, checkLists=checkLists)
    else:
        return render_template('index.html')


# 존재하지 않는 경로에 접근했을 때 404 에러 메시지 출력하기
@app.route('/<path:subpath>', methods=['GET'])
def pathRouting(subpath):
    if subpath not in ['login', 'join', 'checkList', 'exit']:
        notFound = """
        <h1>404 Not Found</h1>
        <h3>/{{ path }}에 대한 페이지를 찾을 수 없습니다.</h3>
        <a href="/">메인 페이지로 이동하기</a>
        """
        return render_template_string(notFound, path=subpath)


# 로그인 요청 처리
@app.route('/login/', methods=['GET', 'POST'])
def login():
    # 해당 경로에 POST 방식으로 요청을 보냈을 때 클라이언트에서 보낸 데이터를 기반으로 
    # 데이터베이스에 질의하여 일치하는 유저가 있는 경우 로그인 승인.
    if request.method == 'POST':
        loginData = request.form.to_dict() # 클라이언트에서 전송한 데이터를 딕셔너리 형태로 가져오기
        connect = sqlite3.connect('test.db')
        connect.row_factory = sqlite3.Row
        connect.execute("PRAGMA foreign_keys = ON;")
        Cursor = connect.cursor()
        # 데이터베이스에 질의를 위한 SELECT문
        selectQuery = f"""
            SELECT * FROM TestUser where 
            email='{loginData['email']}' 
            and pw='{loginData['pw']}';
        """
        Cursor.execute(selectQuery)
        row = Cursor.fetchone()
        connect.commit()
        connect.close()
        
        if row: # SELECT 구문 실행 후 반환값이 있는 경우 클라이언트에게 쿠키를 전달하여 로그인 유지
            res = make_response(redirect('/'))
            res.set_cookie(key='user_id', value=f'{row['id']}')
            return res
        else: # SELECT 구문 실행 이후 아무런 값도 받지 못한 경우
            message = """
                <script>
                    alert('이메일 또는 패스워드를 다시 한 번 확인해 주세요');
                    location.href='/login/';
                </script>
            """
            return render_template_string(message)
        
    return render_template('login.html') # 단순히 GET 요청을 보내 /login/ 경로로 접근한 경우, 'login.html' 템플릿 반환

# 회원가입 요청 처리
@app.route('/join/', methods=['GET', 'POST'])
def join():
    # /join/ 경로로 POST 요청을 보낸 경우, 데이터베이스에 데이터 저장하기
    if request.method == 'POST':
        joinData = request.form.to_dict() # 클라이언트에서 전송된 유저의 데이터
        
        # Testuser 테이블에 저장하기 위한 INSERT문
        insertQuery = f"""
            INSERT INTO TestUser (
            track,
            plan,
            name,
            email,
            pw,
            date
            ) VALUES (
            '{joinData['track']}',
            '{joinData['plan']}',
            '{joinData['name']}',
            '{joinData['email']}',
            '{joinData['pw']}',
            '{datetime.datetime.now().replace(microsecond=0)}'
            );
        """
        connect = sqlite3.connect('test.db')
        connect.execute("PRAGMA foreign_keys = ON;")
        Cursor = connect.cursor()
        Cursor.execute(insertQuery)
        connect.commit()
        connect.close()
        message = """
            <script>
                alert("가입이 완료되었습니다");
                location.href='/login/';
            </script>
        """
        return render_template_string(message) # 가입 완료 메시지와 함께 /login/ 페이지로 리다이렉트
    return render_template('join.html') # 단순히 GET 요청을 보내 해당 경로로 접근한 경우 'join.html' 전달


# 체크리스트 작성 처리
@app.route('/checkList/', methods=['GET', 'POST'])
def postCheckList():
    userid = request.cookies.get('user_id') # 로그인 시 얻을 수 있는 쿠키를 검사해 로그인 상태를 확인하기
    if not userid:
        message = """
            <script>
                alert('해당 기능은 로그인 후 이용하실 수 있습니다');
                location.href='/login/';
            </script>
        """
        return render_template_string(message)
    
    selectQuery = f"""
        SELECT post_id, text FROM CheckList WHERE
        user_id = {userid};
    """

    if request.method == 'POST':
        postData = request.form.to_dict()
        if 'text' in postData:
            if postData['text'] == '':
                return redirect('/checkList/')
        if 'delete' in postData:
            deleteQuery = f"""
                DELETE FROM CheckList
                WHERE post_id={postData['delete']};
            """
            connect = sqlite3.connect('test.db')
            connect.execute("PRAGMA foreign_keys = ON;")
            Cursor = connect.cursor()
            Cursor.execute(deleteQuery)
            connect.commit()
            connect.close()
            return redirect('/checkList/')
        insertQuery = f"""
        INSERT INTO CheckList (
        user_id,
        text,
        date
        ) VALUES (
        {userid},
        '{postData['text']}',
        '{datetime.datetime.now().replace(microsecond=0)}'
        );
        """
        connect = sqlite3.connect('test.db')
        connect.execute("PRAGMA foreign_keys = ON;")
        connect.row_factory = sqlite3.Row
        Cursor = connect.cursor()
        Cursor.execute(insertQuery)
        Cursor.execute(selectQuery)
        checkLists = Cursor.fetchall()
        connect.commit()
        connect.close()
        return render_template('checkList.html', loginState=True, checkLists=checkLists)
    connect = sqlite3.connect('test.db')
    connect.row_factory = sqlite3.Row
    connect.execute("PRAGMA foreign_keys = ON;")
    Cursor = connect.cursor()
    Cursor.execute(selectQuery)
    checkLists = Cursor.fetchall()
    connect.commit()
    connect.close()
    return render_template('checkList.html', loginState=True, checkLists=checkLists)

# 게시판 렌더링
@app.route('/board/', methods=['GET'])
def board():
    userid = request.cookies.get('user_id') # 로그인 시 얻을 수 있는 쿠키를 검사해 로그인 상태를 확인하기
    # 로그인 후 쿠키가 있는 경우 해당 페이지에 접근 허용
    if userid:
        return render_template("board.html", loginState=True)
    
    message = """
        <script>
            alert('해당 기능은 로그인 후 이용하실 수 있습니다');
            location.href='/login/';
        </script>
    """
    return render_template_string(message) # 쿠키가 존재하지 않는 경우 로그인 페이지로 리다이렉트

# 검색 요청 처리
@app.route('/search/', methods=['POST'])
def search():
    data = json.loads(request.data) # 클라이언트에서 요청 보낸 json 포맷 데이터를 가져와 파싱
    print(data)
    exeQuery = data['Query'] # 클라이언트에서 가져온 SELECT 문 실행 쿼리
    print(exeQuery)
    connect = sqlite3.connect("test.db")
    connect.row_factory = sqlite3.Row
    connect.execute("PRAGMA foreign_keys = ON;")
    Cursor = connect.cursor()
    Cursor.execute(exeQuery)
    rows = Cursor.fetchall()
    connect.commit()
    connect.close()

    # 쿼리 실행 이후 반환된 데이터를 딕셔너리로 변환하여 json 포맷으로 클라이언트에게 전달
    data = []
    for row in rows:
        data.append(dict(row))
    print(len(data))
    return jsonify(data)

# 게시글 렌더링
@app.route('/board/view/', methods=['GET'])
def view():
    userid = request.cookies.get('user_id') # 로그인 시 얻을 수 있는 쿠키를 검사해 로그인 상태를 확인하기
    
    if userid:
        return render_template('view.html', loginState=True)
    
    message = """
        <script>
            alert('해당 기능은 로그인 후 이용하실 수 있습니다');
            location.href='/login/';
        </script>
    """
    return render_template_string(message)


# 글 작성 처리
@app.route('/writing/', methods=['GET', 'POST'])
def write():
    userid = request.cookies.get('user_id') # 로그인 시 얻을 수 있는 쿠키를 검사해 로그인 상태를 확인하기
    if not userid: # 로그인 상태가 아닌 경우 메시지 전달과 함께 /login/으로 리다이렉트
        message = """
            <script>
                alert('해당 기능은 로그인 후 이용하실 수 있습니다');
                location.href='/login/';
            </script>
        """
        return render_template_string(message)
    
    # 글 작성 데이터를 보낸 경우
    if request.method == 'POST':
        postData = request.form.to_dict() # 클라이언트에서 보낸 데이터를 딕셔너리로 파싱하기
        
        # 클라이언트에서 입력 폼에 아무런 데이터도 적지 않은 채 요청을 보낸 경우
        if postData['text'] == "" or postData['title'] == "":
            message = """
                <script>
                    alert("제목과 본문을 모두 작성해 주세요");
                    location.href='/writing/';
                </script>
            """
            return render_template_string(message)
        
        # 게시글 업데이트
        if "edit" in postData:
            updateQuery = f"""
                UPDATE board SET 
                title='{postData['title']}',
                text='{postData['text']}'
                WHERE post_id='{postData['post_id']}';
            """
            connect = sqlite3.connect("test.db")
            connect.execute("PRAGMA foreign_keys = ON;")
            Cursor = connect.cursor()
            Cursor.execute(updateQuery)
            connect.commit()
            connect.close()

            message = """
                <script>
                    alert("수정 완료!");
                    location.href='/board/';
                </script>
            """
            return render_template_string(message)
        
        # 게시글 저장 쿼리
        insertQuery = f"""
            INSERT INTO board (
            user_id,
            user_name,
            plan,
            title,
            text,
            date
            ) VALUES (
            {userid},
            (SELECT name FROM TestUser WHERE id='{userid}'),
            (SELECT plan FROM TestUser WHERE id='{userid}'),
            '{postData['title']}',
            '{postData['text']}',
            '{datetime.datetime.now().replace(microsecond=0)}'
            );
        """
        connect = sqlite3.connect("test.db")
        connect.execute("PRAGMA foreign_keys = ON;")
        Cursor = connect.cursor()
        Cursor.execute(insertQuery)
        connect.commit()
        connect.close()

        message = """
            <script>
                alert("작성 완료!");
                location.href='/board/';
            </script>
        """
        return render_template_string(message)
    
    # 게시글 수정 또는 삭제 처리
    param = request.args.get('edit')
    post_id = request.args.get('post_id')
    
    if param == 'delete' and post_id: # 게시글 삭제 처리
        deleteQuery = f"""
            DELETE FROM board WHERE post_id={post_id};
        """
        connect = sqlite3.connect("test.db")
        connect.execute("PRAGMA foreign_keys = ON;")
        Cursor = connect.cursor()
        Cursor.execute(deleteQuery)
        connect.commit()
        connect.close()
        massage = """
            <script>
                alert("글이 삭제되었습니다");
                location.href='/board/';
            </script>
        """
        return render_template_string(massage)
    
    if param == 'modify' and post_id: # 게시글 수정 처리

        # 데이터베이스에서 기존의 데이터를 가져와 입력 폼에 랜더링 할 수 있도록 SELECT 쿼리를 사용함
        selectQuery = f"""
            SELECT * FROM board WHERE post_id='{post_id}';
        """
        connect = sqlite3.connect("test.db")
        connect.row_factory = sqlite3.Row
        connect.execute("PRAGMA foreign_keys = ON;")
        Cursor = connect.cursor()
        Cursor.execute(selectQuery)
        postData = Cursor.fetchone()
        connect.close()
        return render_template("writing.html", loginState=True, postData=postData)

    return render_template('writing.html', loginState=True)

#댓글 작성 처리
@app.route('/api/comment/', methods=['POST'])
def comment():
    data = json.loads(request.data)  # 클라이언트에서 보낸 json 포맷 데이터 파싱하기
    print(data)
    if data['QueryType'] == 'SELECT': # 이미 작성된 댓글을 가져와 브라우저에 출력하는 경우
        exeQuery = data['Query'] # 브라우저에서 전달한 쿼리
        print(data)
        connect = sqlite3.connect("test.db")
        connect.row_factory = sqlite3.Row
        connect.execute("PRAGMA foreign_keys = ON;")
        Cursor = connect.cursor()
        Cursor.execute(exeQuery)
        rows = Cursor.fetchall()
        connect.commit()
        connect.close()
        data = []
        for row in rows:
            data.append(dict(row))
        return jsonify(data) # 쿼리 실행 결과 반환된 데이터 전송
    
    if data['QueryType'] == 'INSERT': # 새로운 댓글을 작성한 경우
        print(data)
        connect = sqlite3.connect("test.db")
        connect.execute("PRAGMA foreign_keys = ON;")
        Cursor = connect.cursor()
        
        # 데이터베이스 삽입을 위한 쿼리
        exeQuery = f"""
            INSERT INTO comment (
            post_id,
            user_name,
            plan,
            text,
            date
            ) VALUES (
            '{data['post_id']}',
            (SELECT name FROM TestUser WHERE id='{data['user_id']}'),
            (SELECT plan FROM TestUser WHERE id='{data['user_id']}'),
            '{data['data']}',
            '{datetime.datetime.now().replace(microsecond=0)}'
            );
        """
        print(exeQuery)
        Cursor.execute(exeQuery)
        connect.commit()
        connect.close()
        return jsonify({"request": "success"})

# 프로필 <------ (해당 기능은 미완성입니다)
@app.route('/profile/')
def profile():
    userid = request.cookies.get('user_id') # 로그인 시 얻을 수 있는 쿠키를 검사해 로그인 상태를 확인하기
    
    return render_template('profile.html', loginState=True)
    

# 로그아웃 처리
@app.route('/logOut/', methods=['GET'])
def logOut():
    message = """
        <script>
            alert("로그아웃 되었습니다");
            location.href='/';
        </script>
    """
    res = make_response(render_template_string(message)) # 응답 객체 생성하기
    res.delete_cookie('user_id') # 로그인 인증을 위해 발급했던 쿠키 제거하기
    return res

# 회원 탈퇴 처리
@app.route('/exit/', methods=['GET', 'POST'])
def exit():
    if request.method == 'POST':
        userData = request.form.to_dict() # 클라이언트에서 전달된 유저의 데이터
        
        # 데이터베이스에서 해당 유저를 삭제하기 위한 DELETE 쿼리
        deleteQuery = f"""
            DELETE FROM TestUser WHERE email='{userData['email']}' and pw='{userData['pw']}';
        """
        connect = sqlite3.connect('test.db')
        connect.execute("PRAGMA foreign_keys = ON;")
        Cursor = connect.cursor()
        Cursor.execute(deleteQuery) # 삭제하기
        connect.commit()
        connect.close()
        message = """
            <script>
                alert("정상적으로 탈퇴 처리 되었습니다");
                location.href='/';
            </script>
        """
        res = make_response(render_template_string(message)) # 응답 객체 생성하기
        res.delete_cookie('user_id') # 발급했던 쿠키 제거하기
        return res
    return render_template('exit.html', loginState=True)


# 템플릿 테스트용
@app.route('/templateTest/')
def test():
    return render_template('test.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) # 도커 파일을 작성하여 컨테이너를 실행하기 위해 같은 네트워크 내 접근을 허용함.
