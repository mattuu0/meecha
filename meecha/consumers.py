 
import json
 
from channels.generic.websocket import AsyncWebsocketConsumer
from accounts.models import CustomUser
from asgiref.sync import sync_to_async
from .models import Friend_data,Friend_request,Geo_Data
from uuid import UUID,uuid4
from django.db.models import Q
from geopy.distance import geodesic

class ChatConsumer(AsyncWebsocketConsumer):
    user_searching = False
    request_searching = False

    async def connect(self):
        user = self.scope["user"]

        #認証済みか
        if not user.is_authenticated:
            await self.close()
            return

        room_id = str(user.userid)

        await self.accept()

        user.now_connected = True
        await self.change_connect_status(user)

        await self.channel_layer.group_add(
            room_id,
            self.channel_name
        )

        #await self.delete_all()

    async def disconnect(self, close_code):
        # Leave room group
        user = self.scope["user"]

        #認証済みか
        if user.is_authenticated:
            room_id = str(user.userid)

            user.now_connected = False
            await self.change_connect_status(user)

            await self.channel_layer.group_discard(room_id, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        user = self.scope["user"]

        #認証されていなかったら戻る
        if not user.is_authenticated:
            await self.close()
            return
        
        data_json = json.loads(text_data)

        command = data_json["command"]
        data = data_json["data"]

        base_dict = {
            "msgtype":"server_msg",
            "data":{}
        }

        if command == "search_user":
            #ユーザー検索

            send_data = await self.search_user(data["username"],user)

            base_dict["data"] = send_data
            await self.send(text_data=json.dumps(base_dict))

        elif command == "friend_request":
            #フレンドリクエスト送信

            #送信先ユーザーid
            to_user = data["userid"]

            #存在しなかったら戻る
            if not await self.check_register_user(str(to_user)):
                return
            
            #同じなら戻る
            if str(user.userid) == str(to_user):
                return
            
            #送信元ユーザーid
            from_user = str(user.userid)

            #フレンドかどうかを確認する
            is_friend,friend_data = await self.check_friend(from_user,to_user)
            if is_friend:
                #フレンドなら何もしない
                send_dict = {
                    "msgtype":"already_friend",
                }
                
                base_dict["data"] = send_dict
                await self.send(text_data=json.dumps(base_dict))

            else:
                #すでにフレンドリクエストを送っているか
                check_register = await self.check_register_request(from_user,to_user)

                if check_register:
                    #既に送信済みの場合エラーメッセージを送る
                    send_dict = {
                        "msgtype":"request_already_sended",
                        "sender_id":str(user.userid)
                    }

                    base_dict["data"] = send_dict

                    await self.send(text_data=json.dumps(base_dict))
                else:
                    #フレンドリクエストを登録する
                    registerd_request = await self.register_request(from_user,to_user)
                    
                    send_dict = {
                        "msgtype":"recv_friend_request",
                        "request_data" : {
                            "requestid":str(registerd_request.dataid),
                            "sender_id":str(user.userid),
                            "username" :str(user.username),
                            "timestamp":str(registerd_request.timestamp.strftime("%Y/%m/%d %H:%M:%S"))
                        }
                    }

                    #フレンドリクエストを送る
                    await self.channel_layer.group_send(  # 指定グループにメッセージを送信する
                        to_user,
                        {
                            'type': 'data_message',
                            'data': send_dict,
                            'user': str(self.scope['user'].userid),
                        }
                    )

        elif command == "get_recved_request":
            #受信済みリクエスト取得

            send_data = await self.get_recved_request(str(user.userid))

            base_dict["data"] = send_data
            await self.send(text_data=json.dumps(base_dict))

        elif command == "get_sended_request":
            #送信済みリクエスト取得

            send_data = await self.get_sended_request(str(user.userid))

            base_dict["data"] = send_data
            await self.send(text_data=json.dumps(base_dict))
            
        elif command == "accept_request":
            #フレンドリクエスト承認
            is_success,friend_data,result_data = await self.accepet_request(data["requestid"],user)

            if is_success:
                send_dict = {
                    "msgtype":"accepted_friend_request",
                    "accept_user":str(friend_data.to_user.userid),
                    "friendid" : str(friend_data.dataid)
                }

                #送信元ユーザーに承認したことを送る
                await self.channel_layer.group_send(  # 指定グループにメッセージを送信する
                    str(friend_data.from_user.userid),
                    {
                        'type': 'data_message',
                        'data': send_dict,
                        'user': str(self.scope['user'].userid),
                    }
                )

                send_dict = {
                    "msgtype":"accepted_friend_request",
                    "request_id" : str(data["requestid"])
                }

                base_dict["data"] = send_dict
                await self.send(text_data=json.dumps(base_dict))
            else:
                await self.send(text_data=json.dumps(result_data))
        elif command == "get_friends":
            #フレンド一覧を取得する
            friends_data = await self.get_friends(user)

            send_dict = {
                "msgtype":"friends_response",
                "friends" : friends_data
            }

            base_dict["data"] = send_dict
            await self.send(text_data=json.dumps(base_dict))
        elif command == "remove_friend":
            #結果
            send_dict = {
                "msgtype":"success_remove_friend",
                "friendid" : data["friendid"]
            }

            if await self.remove_friend(user,data):
                send_dict["msgtype"] = "success_remove_friend"
            else:
                send_dict["msgtype"] = "failed_remove_friend"
            
            #結果を送信する
            base_dict["data"] = send_dict
            await self.send(text_data=json.dumps(base_dict))
        elif command == "update_memo":
            #メモを更新する
            await self.update_memo(user,data)
        
        elif command == "reject_request":
            #結果
            send_dict = {
                "msgtype":"success_reject_friend",
                "requestid" : data["requestid"]
            }

            if await self.reject_request(user,data["requestid"]):
                send_dict["msgtype"] = "success_reject_request"
            else:
                send_dict["msgtype"] = "failed_reject_request"
            
            #結果を送信する
            base_dict["data"] = send_dict
            await self.send(text_data=json.dumps(base_dict))

        elif command == "cancel_request":
            #結果
            send_dict = {
                "msgtype":"success_cancel_friend",
                "requestid" : data["requestid"]
            }

            if await self.cancel_request(user,data["requestid"]):
                send_dict["msgtype"] = "success_cancel_request"
            else:
                send_dict["msgtype"] = "failed_cancel_request"
            
            #結果を送信する
            base_dict["data"] = send_dict
            await self.send(text_data=json.dumps(base_dict))

        elif command == "post_location":
            await self.post_location(user,data)
        else:
            print(data_json)

    #位置情報更新
    @sync_to_async
    def post_location(self,user,data):
        try:
            geo_data = Geo_Data.objects.get(user = user)

            geo_data.latitude = data["latitude"]
            geo_data.longitude = data["longitude"]

            geo_data.save()
            
            #フレンドを検索する
            friends = Friend_data.objects.filter(Q(to_user = user) | Q(from_user = user))

            for friend in friends.all():
                if friend.from_user == user:
                    friend_user = friend.to_user
                else:
                    friend_user = friend.from_user
                
                #位置情報取得
                check_friend_geo = Geo_Data.objects.filter(user = friend_user)
                
                #位置情報が登録されていなかったら戻る
                if not check_friend_geo.exists():
                    continue
                
                #フレンドデータ
                friend_geo_data = check_friend_geo.get(user = friend_user)

                #自身の位置情報
                myself_latitude = float(data["latitude"])
                myself_longitude = float(data["longitude"])

                #フレンドの位置情報
                friend_latitube = friend_geo_data.latitude
                friend_longitude = friend_geo_data.longitude

                #距離をメートルで取得
                distance_m = geodesic([myself_latitude,myself_longitude],[friend_latitube,friend_longitude]).m

                

        except Geo_Data.DoesNotExist:
            geo_data = Geo_Data()

            geo_data.latitude = data["latitude"]
            geo_data.longitude = data["longitude"]
            geo_data.user = user

            geo_data.save()

        except:
            import traceback
            traceback.print_exc()

            return False
        
        return True

    #フレンドを削除する
    @sync_to_async
    def remove_friend(self,user,data) -> bool:
        try:
            from_user = str(user.userid)
            
            #フレンドID
            friendid = str(data["friendid"])

            friend_data = Friend_data.objects.filter(dataid = friendid)

            #フレンドデータが存在しない (フレンドじゃない) なら戻る
            if not friend_data.exists():
                return False
            
            #指定したIDのフレンドが存在するか
            check_user = friend_data.filter(Q(to_user = from_user) | Q(from_user = from_user))

            #フレンドデータに (ユーザーが含まれているか)
            if not check_user.exists():
                return False
            
            #フレンドを削除する
            check_user.delete()

            return True
        except:
            import traceback
            traceback.print_exc()

        return False
    
    #フレンドリクエストを拒否する
    @sync_to_async
    def reject_request(self,user,requestid) -> bool:
        try:
           
            check_request = Friend_request.objects.filter(dataid =  UUID(requestid))

            #リクエストが存在するか
            if not check_request.exists():
                return False
            
            #拒否しようとしているユーザー宛か
            check_user = check_request.filter(to_user = user)

            if not check_user.exists():
                return False
            
            for registered_data in check_user.all():
                #リクエストを削除する
                registered_data.delete()
            
            return True
        except:
            import traceback
            traceback.print_exc()

        return False
    
    #フレンドリクエストをキャンセルする
    @sync_to_async
    def cancel_request(self,user,requestid) -> bool:
        try:
           
            check_request = Friend_request.objects.filter(dataid =  UUID(requestid))

            #リクエストが存在するか
            if not check_request.exists():
                return False
            
            #拒否しようとしているユーザー宛か
            check_user = check_request.filter(from_user = user)

            if not check_user.exists():
                return False
            
            for registered_data in check_user.all():
                #リクエストを削除する
                registered_data.delete()
            
            return True
        except:
            import traceback
            traceback.print_exc()

        return False

    #メモを更新する
    @sync_to_async
    def update_memo(self,user,data):
        from_user = str(user.userid)
        
        #フレンドかどうかをチェックする
        is_friend,friend_data = self.check_friend_sync(from_user,data["friendid"])

        if is_friend:
            memo_value = data["uodate_memo"]

            #フレンドで更新対象がfrom_userか
            if friend_data.from_user == user:
                friend_data.to_user_memo = memo_value
            else:
                friend_data.from_user_memo = memo_value
            
            #更新する
            friend_data.save()

    @sync_to_async 
    def accepet_request(self,requestid,acceptuser):
        filter_requests = Friend_request.objects.filter(dataid = requestid)

        if not filter_requests.exists():
            #リクエストが存在しなかったら戻る
            return False,"",{
                "msgtype":"request_accpet_error",
                "requestid" : requestid
            }
        
        #リクエストを取得する
        try:
            #宛先ユーザーが一致するか確認する
            request = filter_requests.get(to_user = acceptuser)

            #フレンド情報を登録する
            register_data = Friend_data()
            register_data.to_user = acceptuser
            register_data.from_user = request.from_user
            register_data.dataid = uuid4()
            register_data.save()

            #フレンドリクエストを削除する
            request.delete()

            return True,register_data, {
                "msgtype":"request_accpet_success",
                "requestid" : requestid
            }

        except Friend_request.DoesNotExist:
            return False,"", {
                "msgtype":"request_accpet_error",
                "requestid" : requestid
            }
        
        except:
            return False,"", {
                "msgtype":"request_accpet_error",
                "requestid" : requestid
            }

    @sync_to_async
    def delete_all(self):
        Friend_request.objects.all().delete()
        Friend_data.objects.all().delete()

    @sync_to_async
    def change_connect_status(self,user) -> bool:
        user.save()
    
    @sync_to_async
    def get_friends(self,user) -> list:
        return self.get_friends_sync(user)

    def get_friends_sync(self,user) -> list:
        friends = Friend_data.objects.filter(Q(to_user = user) | Q(from_user = user))

        result_list = []
        for friend in friends.all():
            if friend.from_user == user:
                friend_user = friend.to_user
                memo_data = friend.to_user_memo
            else:
                friend_user = friend.from_user
                memo_data = friend.from_user_memo
            
            result_list.append({
                "friendid" : str(friend.dataid),
                "friend_userid" : str(friend_user.userid),
                "friend_username" : str(friend_user.username),
                "friend_memo" : str(memo_data),
                "friend_timestamp" : str(friend.timestamp)
            })
        
        return result_list

    @sync_to_async
    def search_user(self,username,user):
        #すでに検索中なら戻る
        if self.user_searching:
            return
        
        #検索中に設定
        self.user_searching = True

        send_dict = {
            "msgtype":"search_response",
            "match_users":{}
        }

        try:
            #ユーザー検索
            #TODO results = CustomUser.objects.filter(username=username).all()
            results = CustomUser.objects.filter(username__contains=username).all()

            #結果
            for match_user in results:
                user_dict = {}

                user_dict["user_name"] = match_user.username                #ユーザーメイ

                #フレンドか
                is_friend,friend_data = self.check_friend_sync(str(user.userid),str(match_user.userid))
                if is_friend:
                    user_dict["is_friend"] = "1"      
                else:
                    user_dict["is_friend"] = "0"

                send_dict["match_users"][str(match_user.userid)] = user_dict

        except:
            import traceback
            traceback.print_exc()

        #検索宙を解除
        self.user_searching = False
        return send_dict
    
    #受け取ったリクエスト
    @sync_to_async
    def get_recved_request(self,userid):
        #すでに検索中なら戻る
        if self.request_searching:
            return
        
        #検索中に設定
        self.request_searching = True

        send_dict = {
            "msgtype":"recved_friend_request",
            "recved_requests":{}
        }

        to_user = CustomUser.objects.get(userid = userid)

        try:
            #ユーザー検索
            #TODO results = CustomUser.objects.filter(username=username).all()
            results = Friend_request.objects.filter(to_user = to_user).all()

            #結果
            for request_data in results:
                request_dict = {}

                request_dict["user_name"] = str(request_data.from_user.username)                    #送信元ユーザー名
                request_dict["sender_userid"] = str(request_data.from_user.userid)                  #送信元ユーザー名
                request_dict["timestamp"] = request_data.timestamp.strftime("%Y/%m/%d %H:%M:%S")    #送信日時

                send_dict["recved_requests"][str(request_data.dataid)] = request_dict

        except:
            import traceback
            traceback.print_exc()

        #検索宙を解除
        self.request_searching = False
        return send_dict
    
    @sync_to_async
    def get_sended_request(self,userid):
        #すでに検索中なら戻る
        if self.request_searching:
            return
        
        #検索中に設定
        self.request_searching = True

        send_dict = {
            "msgtype":"sended_friend_request",
            "sended_requests":{}
        }

        from_user = CustomUser.objects.get(userid = userid)

        try:
            #ユーザー検索
            #TODO results = CustomUser.objects.filter(username=username).all()
            results = Friend_request.objects.filter(from_user = from_user).all()

            #結果
            for request_data in results:
                request_dict = {}

                request_dict["user_name"] = str(request_data.to_user.username)                    #送信元ユーザー名
                request_dict["sender_id"] = str(request_data.to_user.userid)                  #送信元ユーザー名
                request_dict["timestamp"] = request_data.timestamp.strftime("%Y/%m/%d %H:%M:%S")    #送信日時

                send_dict["sended_requests"][str(request_data.dataid)] = request_dict

        except:
            import traceback
            traceback.print_exc()

        #検索宙を解除
        self.request_searching = False
        return send_dict

    @sync_to_async
    def register_request(self,from_user:str,to_user:str) -> Friend_request:
        to_user = CustomUser.objects.get(userid = to_user)
        from_user = CustomUser.objects.get(userid = from_user)

        request_obj = Friend_request()
        request_obj.from_user = from_user
        request_obj.to_user = to_user
        request_obj.dataid = uuid4()

        request_obj.save()

        return request_obj
    
    @sync_to_async
    def check_friend(self,from_user:str,to_user:str):
        return self.check_friend_sync(from_user,to_user)

    def check_friend_sync(self,from_user:str,to_user:str):
        try:
            to_user = CustomUser.objects.get(userid = to_user)
            from_user = CustomUser.objects.get(userid = from_user) 

            try:
                #フレンドレコードに入っているか
                check_friend = Friend_data.objects.filter(Q(to_user = from_user) | Q(from_user = from_user))

                #ある場合
                if check_friend.exists():
                    #フレンドIDが一致するか
                    check_reverse_filter = check_friend.filter(Q(to_user = to_user) | Q(from_user = to_user))
        
                    if check_reverse_filter.exists():
                        return True,check_reverse_filter.get(Q(to_user = to_user) | Q(from_user = to_user))
                else:
                    return False,None
            
            except Friend_data.DoesNotExist:
                pass

            except:
                import traceback
                traceback.print_exc()
        
        except CustomUser.DoesNotExist:
            pass
        except:
            import traceback
            traceback.print_exc()
        
        return False,None
    
    @sync_to_async
    def check_register_request(self,from_user:str,to_user:str) -> bool:
        try:
            to_user = CustomUser.objects.get(userid = to_user)
            from_user = CustomUser.objects.get(userid = from_user) 

            try:
                #フレンドレコードに入っているか
                check_request = Friend_request.objects.filter(Q(to_user = from_user) | Q(from_user = from_user))

                #ある場合
                if check_request.exists():
                    #フレンドIDが一致するか
                    return check_request.filter(Q(to_user = to_user) | Q(from_user = to_user)).exists()
                else:
                    return False
            except:
                import traceback
                traceback.print_exc()
            
        except:
            import traceback
            traceback.print_exc()
        
        return False

    @sync_to_async
    def check_register_user(self,checkid) -> bool:
        return CustomUser.objects.filter(userid = checkid).exists()

    async def data_message(self, event):
        print("data message")

        # グループメッセージを受け取る
        user = event['user']

        await self.send(text_data=json.dumps({
            "msgtype":"server_msg",
            "data":event["data"],
            'user': user,
        }))

    """
    async def chat_message(self, event):
        # グループメッセージを受け取る
        message = event['data']
        user = event['user']
        # websocket でメッセージを送信する
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'user': user,
        }))

    # Receive message from room group
    async def send_message(self, event):
        message = event["data"]-p0--0\-^^

 
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"data": message}))
    """


"""
room_id = str(user.userid)

        await self.channel_layer.group_send(  # 指定グループにメッセージを送信する
            "93977bc4-5819-4529-bc00-926f8e3398da",
            {
                'type': 'chat_message',
                'message': "hello",
                'user': str(self.scope['user'].userid),
            }
        )
"""