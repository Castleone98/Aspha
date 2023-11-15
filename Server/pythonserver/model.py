## 라이브러리 ##
import sys
from collections import defaultdict

import pandas as pd
import torch
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from torch import nn, Tensor
from torch_geometric.nn.conv import MessagePassing
from torch_geometric.nn.conv.gcn_conv import gcn_norm
from torch_sparse import SparseTensor


# graph의 형태로 변환하는 함수
def load_edge_csv(df, src_index_col, dst_index_col, link_index_col, rating_threshold=3.5):
    edge_index = None
    src = [user_id for user_id in df["나이성별"]]

    num_users = len(df["나이성별"].unique())

    dst = [(item_id) for item_id in df["차량아이디"]]

    link_vals = df[link_index_col].values

    edge_attr = (
        torch.from_numpy(df[link_index_col].values).view(-1, 1).to(torch.long)
        >= rating_threshold
    )

    # 평점이 들어감
    edge_values = []
    # src에는 회원번호가 dst에는 차량아이디
    edge_index = [[], []]

    for i in range(edge_attr.shape[0]):
        if edge_attr[i]:
            edge_index[0].append(src[i])
            edge_index[1].append(dst[i])
            edge_values.append(link_vals[i])

    return edge_index, edge_values


# R matrix는 사용자와 아이템의 상호작용 matrix이다
# user와 item이 연결되면 1 연결되지 않으면 0을 나타낸다
# R matrix를 transfer하여 기존 R matrix와 결합하면 adjaction matrix가 된다
# R matrix를 adjaction matrix로 변환하는 함수이다
def convert_r_mat_edge_index_to_adj_mat_edge_index(input_edge_index, input_edge_values):
    R = torch.zeros((num_users, num_items))
    for i in range(len(input_edge_index[0])):
        row_idx = input_edge_index[0][i]
        col_idx = input_edge_index[1][i]
        R[row_idx][col_idx] = input_edge_values[i]
    R_transpose = torch.transpose(R, 0, 1)

    adj_mat = torch.zeros((num_users + num_items, num_users + num_items))
    adj_mat[:num_users, num_users:] = R.clone()
    adj_mat[num_users:, :num_users] = R_transpose.clone()

    adj_mat_coo = adj_mat.to_sparse_coo()
    adj_mat_coo_indices = adj_mat_coo.indices()
    adj_mat_coo_values = adj_mat_coo.values()

    return adj_mat_coo_indices, adj_mat_coo_values


# adjaction matrix를 R matrix로 변환하는 함수이다.
def convert_adj_mat_edge_index_to_r_mat_edge_index(input_edge_index, input_edge_values):
    device = input_edge_values.device
    input_edge_index = input_edge_index.to(device)

    sparse_input_edge_index = SparseTensor(
        row=input_edge_index[0],
        col=input_edge_index[1],
        value=input_edge_values,
        sparse_sizes=((num_users + num_items), num_users + num_items),
    )

    adj_mat = sparse_input_edge_index.to_dense()
    interact_mat = adj_mat[:num_users, num_users:]

    r_mat_edge_index = interact_mat.to_sparse_coo().indices()
    r_mat_edge_values = interact_mat.to_sparse_coo().values()

    return r_mat_edge_index, r_mat_edge_values


class LightGCN(MessagePassing):
    def __init__(
        self,
        num_users,
        num_items,
        embedding_dim=64,
        K=3,
        add_self_loops=False,
        dropout_rate=0.1,
    ):
        super().__init__()
        self.dropout_rate = dropout_rate
        self.num_users = num_users
        self.num_items = num_items
        self.embedding_dim = embedding_dim
        # 이웃 확산 스텝 수
        self.K = K
        # self loop 엣지 추가 여부 default = False
        self.add_self_loops = add_self_loops

        # user 임베딩
        self.users_emb = nn.Embedding(
            num_embeddings=self.num_users, embedding_dim=self.embedding_dim
        )

        # item 임베딩
        self.items_emb = nn.Embedding(
            num_embeddings=self.num_items, embedding_dim=self.embedding_dim
        )

        nn.init.normal_(self.users_emb.weight, std=0.1)
        nn.init.normal_(self.items_emb.weight, std=0.1)

        self.out = nn.Linear(embedding_dim + embedding_dim, 1)

    def forward(self, edge_index: Tensor, edge_values: Tensor):
        # 정규화
        edge_index_norm = gcn_norm(
            edge_index=edge_index, add_self_loops=self.add_self_loops
        )

        # 초기 임베딩 사용자와 아이템의 가중치 연결
        # 하나의 행렬로 합침
        emb_0 = torch.cat([self.users_emb.weight, self.items_emb.weight])

        embs = [emb_0]

        emb_k = emb_0
        # K번 반복하면서 propagate 실행
        # emb_k 업데이트
        for i in range(self.K):
            emb_k = self.propagate(
                edge_index=edge_index_norm[0], x=emb_k, norm=edge_index_norm[1]
            )
            embs.append(emb_k)

        embs = torch.stack(embs, dim=1)
        # 최종 임베딩
        emb_final = torch.mean(embs, dim=1)

        # 사용자와 아이템으로 분리
        users_emb_final, items_emb_final = torch.split(
            emb_final, [self.num_users, self.num_items]
        )

        r_mat_edge_index, _ = convert_adj_mat_edge_index_to_r_mat_edge_index(
            edge_index, edge_values
        )

        src, dest = r_mat_edge_index[0], r_mat_edge_index[1]

        user_embeds = users_emb_final[src]
        item_embeds = items_emb_final[dest]

        output = torch.cat([user_embeds, item_embeds], dim=1)

        output = self.out(output)

        return output

    def message(self, x_j, norm):
        return norm.view(-1, 1) * x_j


def load_model_with_additional_info(path, model_class):
    checkpoint = torch.load(path, map_location=torch.device("cpu"))
    model = model_class(
        num_users=checkpoint["num_users"], num_items=checkpoint["num_items"]
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    return model, checkpoint["num_users"], checkpoint["num_items"]


model, num_users, num_items = load_model_with_additional_info(
    "model_with_info.pth", LightGCN
)


if __name__ == "__main__":
    print(f"f1")
    df = pd.read_csv("Kaflix_차량아이디.csv")
    print(f"f2")
    df = df.sort_values("나이성별")

    user = preprocessing.LabelEncoder()
    item = preprocessing.LabelEncoder()

    df.나이성별 = user.fit_transform(df.나이성별.values)
    df.차량아이디 = item.fit_transform(df.차량아이디.values)

    print(f"f3")
    # 표준 입력으로부터 받은 문자열 읽기
    combined_input = sys.stdin.read()
    code_str, view_str = combined_input.split(',')

    print(f"{combined_input}")

    # 문자열을 원래의 데이터 타입으로 변환
    encoded_data_from_app = int(code_str)
    encoded_view = int(view_str)

    # print(f"encoded_view:{encoded_view}")
    print(f"recommended_items:{encoded_data_from_app}")

    # src : 나이성별
    # dst : 차량아이디
    # edge : count
    edge_index, edge_values = load_edge_csv(
        df,
        src_index_col="나이성별",
        dst_index_col="차량아이디",
        link_index_col="scaled_차량아이디_빈도수",
        # edge 판단 기준 threshold 설정
        rating_threshold=1,
    )

    # torch 형태로 변형
    edge_index = torch.LongTensor(edge_index)
    edge_values = torch.tensor(edge_values)

    num_users = len(df["나이성별"].unique())
    num_items = len(df["차량아이디"].unique())



    print(f"num_users {num_users}, num_items {num_items}")

    num_interactions = edge_index.shape[1]
    all_indices = [i for i in range(num_interactions)]

    train_indices, test_indices = train_test_split(all_indices, test_size=0.3, random_state=1)
    val_indices, test_indices = train_test_split(test_indices, test_size=0.5, random_state=1)

    train_edge_index = edge_index[:, train_indices]
    train_edge_value = edge_values[train_indices]

    val_edge_index = edge_index[:, val_indices]
    val_edge_value = edge_values[val_indices]

    test_index = edge_index[:, test_indices]
    test_value = edge_values[test_indices]


    mask = test_index[0] == int(encoded_data_from_app)
    test_edge_index = test_index[:, mask]
    test_edge_values = test_value[mask]

    test_edge_index, test_edge_values = convert_r_mat_edge_index_to_adj_mat_edge_index(test_edge_index, test_edge_values)

    (
        r_mat_test_edge_index,
        r_mat_test_edge_values,
    ) = convert_adj_mat_edge_index_to_r_mat_edge_index(
        test_edge_index, test_edge_values
    )

    pred_ratings = model.forward(test_edge_index, test_edge_values)

    user_item_rating_list = defaultdict(list)
    recommended_items = defaultdict(list)
    item_recommend_count = defaultdict(int)

    for i in range(len(r_mat_test_edge_index[0])):
        src = r_mat_test_edge_index[0][i].item()
        dest = r_mat_test_edge_index[1][i].item()
        true_rating = r_mat_test_edge_values[i].item()
        pred_rating = pred_ratings[i].item()
        user_item_rating_list[src].append((dest, pred_rating, true_rating))

    k = encoded_view
    for user_id, user_ratings in user_item_rating_list.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)  # pred_rating 기준으로 정렬 변경

        top_k_items = [
            item_id for (item_id, pred_rating, true_rating) in user_ratings[:k]
        ]
        recommended_items[user_id].extend(top_k_items)  # 추천된 아이템 저장

        for item_id in top_k_items:
            item_recommend_count[item_id] += 1

    user_item_rating_list, recommended_items, item_recommend_count


    print(recommended_items)
    print(user_item_rating_list)
    print(item_recommend_count)
